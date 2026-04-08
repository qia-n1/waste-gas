from __future__ import annotations

import math

import torch
import torch.nn as nn
import torch.nn.functional as F

from .config import ModelConfig
from .vendor import ensure_mamba_ssm_importable

ensure_mamba_ssm_importable()

from mamba_ssm.modules.mamba3 import Mamba3  # noqa: E402


def _patch_mamba3_fallback_for_legacy_cuda() -> None:
    original = getattr(Mamba3, "_use_torch_fallback", None)
    if original is None or getattr(Mamba3, "_vocsmamba_fallback_patched", False):
        return

    def _patched(self, tensor: torch.Tensor) -> bool:
        if tensor.device.type == "cuda":
            major, minor = torch.cuda.get_device_capability(tensor.device)
            # Triton kernels used by current Mamba3 path require sm_75+.
            if (major, minor) < (7, 5):
                return True
        return original(self, tensor)

    Mamba3._use_torch_fallback = _patched  # type: ignore[assignment]
    Mamba3._vocsmamba_fallback_patched = True  # type: ignore[attr-defined]


_patch_mamba3_fallback_for_legacy_cuda()


def count_parameters(model: nn.Module) -> int:
    return sum(param.numel() for param in model.parameters())


class VocsMambaBlock(nn.Module):
    def __init__(self, config: ModelConfig):
        super().__init__()
        self.residual_scale_mixer = config.residual_scale_mixer
        self.residual_scale_ffn = config.residual_scale_ffn
        self.norm = nn.LayerNorm(config.d_model)
        self.mixer = Mamba3(
            d_model=config.d_model,
            d_state=config.d_state,
            expand=config.expand,
            headdim=config.headdim,
            rope_fraction=config.rope_fraction,
            chunk_size=config.chunk_size,
            is_mimo=config.is_mimo,
        )
        self.dropout = nn.Dropout(config.dropout)
        self.ffn_norm = nn.LayerNorm(config.d_model)
        ff_hidden = config.d_model * config.ff_mult
        self.ffn = nn.Sequential(
            nn.Linear(config.d_model, ff_hidden),
            nn.SiLU(),
            nn.Dropout(config.dropout),
            nn.Linear(ff_hidden, config.d_model),
        )

    def forward(self, hidden_states: torch.Tensor) -> torch.Tensor:
        mixed = self.mixer(self.norm(hidden_states))
        hidden_states = hidden_states + self.dropout(mixed * self.residual_scale_mixer)
        ffn_out = self.ffn(self.ffn_norm(hidden_states))
        hidden_states = hidden_states + self.dropout(ffn_out * self.residual_scale_ffn)
        return hidden_states


class VocsMambaForecaster(nn.Module):
    def __init__(self, input_dim: int, config: ModelConfig, pred_len: int):
        super().__init__()
        self.config = config
        self.pred_len = pred_len
        self.use_multi_horizon_heads = config.use_multi_horizon_heads
        self.enable_exceed_aux_head = config.enable_exceed_aux_head
        self.predict_delta_from_last = config.predict_delta_from_last
        self.input_proj = nn.Sequential(
            nn.Linear(input_dim, config.d_model),
            nn.LayerNorm(config.d_model),
        )
        self.layers = nn.ModuleList([VocsMambaBlock(config) for _ in range(config.n_layer)])
        self.final_norm = nn.LayerNorm(config.d_model)
        def build_head(out_dim: int) -> nn.Sequential:
            return nn.Sequential(
                nn.Linear(config.d_model * 2, config.d_model),
                nn.SiLU(),
                nn.Dropout(config.dropout),
                nn.Linear(config.d_model, out_dim),
            )

        if self.use_multi_horizon_heads:
            self.short_horizon = max(1, min(config.short_horizon, pred_len))
            remaining = max(0, pred_len - self.short_horizon)
            self.medium_horizon = max(0, min(config.medium_horizon, remaining))
            self.long_horizon = pred_len - self.short_horizon - self.medium_horizon
            self.short_head = build_head(self.short_horizon)
            self.medium_head = build_head(self.medium_horizon) if self.medium_horizon > 0 else None
            self.long_head = build_head(self.long_horizon) if self.long_horizon > 0 else None
            self.head = None
        else:
            self.head = build_head(pred_len)
            self.short_head = None
            self.medium_head = None
            self.long_head = None
        if self.enable_exceed_aux_head:
            self.exceed_head = nn.Sequential(
                nn.Linear(config.d_model * 2, config.aux_head_hidden),
                nn.SiLU(),
                nn.Dropout(config.dropout),
                nn.Linear(config.aux_head_hidden, pred_len),
            )
        else:
            self.exceed_head = None

        total_params = count_parameters(self)
        if total_params > config.max_parameters:
            raise ValueError(
                f"Model has {total_params:,} parameters, exceeding the 880M cap ({config.max_parameters:,})."
            )

    def forward(self, inputs: torch.Tensor, return_aux: bool = False):
        hidden_states = self.input_proj(inputs)
        for layer in self.layers:
            hidden_states = layer(hidden_states)
        hidden_states = self.final_norm(hidden_states)
        summary = torch.cat([hidden_states[:, -1], hidden_states.mean(dim=1)], dim=-1)
        if self.use_multi_horizon_heads:
            chunks = [self.short_head(summary)]
            if self.medium_head is not None:
                chunks.append(self.medium_head(summary))
            if self.long_head is not None:
                chunks.append(self.long_head(summary))
            predictions = torch.cat(chunks, dim=-1).unsqueeze(-1)
        else:
            predictions = self.head(summary).unsqueeze(-1)
        if self.predict_delta_from_last:
            # Inputs are built as [engineered_features, historical_target], so the last channel
            # at the last timestep is the latest observed target value.
            last_target = inputs[:, -1:, -1:]
            predictions = predictions + last_target
        if return_aux and self.exceed_head is not None:
            exceed_logits = self.exceed_head(summary)
            return predictions, exceed_logits
        return predictions


class SinusoidalTimeEmbedding(nn.Module):
    def __init__(self, dim: int):
        super().__init__()
        self.dim = dim

    def forward(self, timesteps: torch.Tensor) -> torch.Tensor:
        half_dim = self.dim // 2
        if half_dim == 0:
            return torch.zeros((timesteps.shape[0], 0), device=timesteps.device)
        scale = torch.log(torch.tensor(10000.0, device=timesteps.device)) / max(half_dim - 1, 1)
        freqs = torch.exp(torch.arange(half_dim, device=timesteps.device) * -scale)
        angles = timesteps.float().unsqueeze(1) * freqs.unsqueeze(0)
        emb = torch.cat([torch.sin(angles), torch.cos(angles)], dim=1)
        if self.dim % 2 == 1:
            emb = torch.cat([emb, torch.zeros_like(emb[:, :1])], dim=1)
        return emb


class ProbSparseSelfAttention(nn.Module):
    """Approximate sparse attention by keeping top-k keys per query."""

    def __init__(self, d_model: int, n_heads: int, topk: int, dropout: float):
        super().__init__()
        if d_model % n_heads != 0:
            raise ValueError("d_model must be divisible by n_heads for ProbSparseSelfAttention.")
        self.d_model = d_model
        self.n_heads = n_heads
        self.head_dim = d_model // n_heads
        self.topk = max(1, topk)
        self.qkv = nn.Linear(d_model, d_model * 3)
        self.out_proj = nn.Linear(d_model, d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: [B, L, C]
        bsz, seqlen, _ = x.shape
        qkv = self.qkv(x).reshape(bsz, seqlen, 3, self.n_heads, self.head_dim)
        q, k, v = qkv.unbind(dim=2)
        # [B, H, L, D]
        q = q.transpose(1, 2)
        k = k.transpose(1, 2)
        v = v.transpose(1, 2)

        scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.head_dim)
        if self.topk < seqlen:
            topk_vals, topk_idx = torch.topk(scores, k=self.topk, dim=-1)
            sparse_scores = torch.full_like(scores, torch.finfo(scores.dtype).min)
            sparse_scores.scatter_(-1, topk_idx, topk_vals)
            scores = sparse_scores
        attn = torch.softmax(scores, dim=-1)
        attn = self.dropout(attn)
        context = torch.matmul(attn, v)
        context = context.transpose(1, 2).reshape(bsz, seqlen, self.d_model)
        return self.out_proj(context)


class InformerStyleEncoderLayer(nn.Module):
    def __init__(self, d_model: int, n_heads: int, topk: int, dropout: float, ff_mult: int):
        super().__init__()
        self.norm1 = nn.LayerNorm(d_model)
        self.attn = ProbSparseSelfAttention(d_model=d_model, n_heads=n_heads, topk=topk, dropout=dropout)
        self.norm2 = nn.LayerNorm(d_model)
        ff_dim = d_model * ff_mult
        self.ffn = nn.Sequential(
            nn.Linear(d_model, ff_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(ff_dim, d_model),
        )
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.dropout(self.attn(self.norm1(x)))
        x = x + self.dropout(self.ffn(self.norm2(x)))
        return x


class MovingAverageDecomp(nn.Module):
    def __init__(self, kernel_size: int = 25):
        super().__init__()
        self.kernel_size = kernel_size

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        # x: [B, L, C]
        trend = F.avg_pool1d(
            x.transpose(1, 2),
            kernel_size=self.kernel_size,
            stride=1,
            padding=self.kernel_size // 2,
        ).transpose(1, 2)
        seasonal = x - trend
        return seasonal, trend


class AutoformerStyleEncoderLayer(nn.Module):
    def __init__(self, d_model: int, n_heads: int, topk: int, dropout: float, ff_mult: int):
        super().__init__()
        self.decomp = MovingAverageDecomp(kernel_size=25)
        self.attn_block = InformerStyleEncoderLayer(
            d_model=d_model,
            n_heads=n_heads,
            topk=topk,
            dropout=dropout,
            ff_mult=ff_mult,
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        seasonal, trend = self.decomp(x)
        seasonal = self.attn_block(seasonal)
        return seasonal + trend


class TemporalConditionEmbedding(nn.Module):
    """
    Build temporal cues from hour/weekday cyclical features if indices are provided.
    Expected order in indices: hour_sin, hour_cos, weekday_sin, weekday_cos.
    """

    def __init__(
        self,
        d_model: int,
        temporal_embed_dim: int,
        time_feature_indices: tuple[int, ...],
        use_weekend_gate: bool,
    ):
        super().__init__()
        self.time_feature_indices = tuple(time_feature_indices)
        self.use_weekend_gate = use_weekend_gate
        in_dim = len(self.time_feature_indices)
        if in_dim > 0:
            self.time_proj = nn.Sequential(
                nn.Linear(in_dim, temporal_embed_dim),
                nn.SiLU(),
                nn.Linear(temporal_embed_dim, d_model),
            )
        else:
            self.time_proj = None

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        # inputs: [B, L, N]
        if self.time_proj is None:
            return torch.zeros(inputs.shape[0], inputs.shape[1], 1, device=inputs.device).expand(-1, -1, 0)

        time_feats = inputs[..., list(self.time_feature_indices)]
        time_embed = self.time_proj(time_feats)

        if self.use_weekend_gate and len(self.time_feature_indices) >= 4:
            # Recover weekday index from sin/cos and attenuate weekday-vs-weekend patterns.
            wd_sin = time_feats[..., 2]
            wd_cos = time_feats[..., 3]
            wd_angle = torch.atan2(wd_sin, wd_cos)
            wd_idx = (wd_angle * 7.0 / (2.0 * math.pi)) % 7.0
            weekend_gate = ((wd_idx >= 5.0).float() * 0.25 + 0.875).unsqueeze(-1)
            time_embed = time_embed * weekend_gate

        return time_embed


class ConditioningStack(nn.Module):
    def __init__(self, input_dim: int, config: ModelConfig):
        super().__init__()
        self.config = config
        self.kind = config.diffusion_conditioning_type
        self.in_proj = nn.Sequential(
            nn.Linear(input_dim, config.d_model),
            nn.LayerNorm(config.d_model),
        )
        self.temporal = TemporalConditionEmbedding(
            d_model=config.d_model,
            temporal_embed_dim=config.diffusion_temporal_embed_dim,
            time_feature_indices=tuple(config.diffusion_time_feature_indices),
            use_weekend_gate=config.diffusion_use_weekend_gate,
        )
        n_heads = max(1, config.d_model // max(1, config.headdim))

        if self.kind == "informer":
            self.layers = nn.ModuleList(
                [
                    InformerStyleEncoderLayer(
                        d_model=config.d_model,
                        n_heads=n_heads,
                        topk=config.diffusion_prob_sparse_topk,
                        dropout=config.dropout,
                        ff_mult=config.ff_mult,
                    )
                    for _ in range(config.diffusion_conditioning_layers)
                ]
            )
        elif self.kind == "autoformer":
            self.layers = nn.ModuleList(
                [
                    AutoformerStyleEncoderLayer(
                        d_model=config.d_model,
                        n_heads=n_heads,
                        topk=config.diffusion_prob_sparse_topk,
                        dropout=config.dropout,
                        ff_mult=config.ff_mult,
                    )
                    for _ in range(config.diffusion_conditioning_layers)
                ]
            )
        else:
            self.layers = nn.ModuleList([VocsMambaBlock(config) for _ in range(config.n_layer)])

        self.final_norm = nn.LayerNorm(config.d_model)
        self.cond_proj = nn.Linear(config.d_model * 2, config.d_model)

    def forward(self, inputs: torch.Tensor, pred_len: int) -> tuple[torch.Tensor, torch.Tensor]:
        h = self.in_proj(inputs)
        t_embed = self.temporal(inputs)
        if t_embed.numel() > 0:
            h = h + t_embed
        for layer in self.layers:
            h = layer(h)
        h = self.final_norm(h)
        summary = torch.cat([h[:, -1], h.mean(dim=1)], dim=-1)
        cond = self.cond_proj(summary).unsqueeze(1).expand(-1, pred_len, -1)
        return cond, summary


class ConditionalResBlock1D(nn.Module):
    def __init__(self, d_model: int, cond_dim: int, dropout: float):
        super().__init__()
        self.norm = nn.LayerNorm(d_model)
        self.net = nn.Sequential(
            nn.Linear(d_model, d_model),
            nn.SiLU(),
            nn.Dropout(dropout),
            nn.Linear(d_model, d_model),
        )
        self.film = nn.Linear(cond_dim, d_model * 2)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor, cond: torch.Tensor) -> torch.Tensor:
        # x, cond: [B, L, C]
        gamma, beta = self.film(cond).chunk(2, dim=-1)
        h = self.norm(x)
        h = h * (1.0 + torch.tanh(gamma)) + beta
        h = self.net(h)
        return x + self.dropout(h)


class TransformerDenoiser(nn.Module):
    def __init__(self, config: ModelConfig):
        super().__init__()
        n_heads = max(1, config.d_model // max(1, config.headdim))
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=config.d_model,
            nhead=n_heads,
            dim_feedforward=config.d_model * config.ff_mult,
            dropout=config.dropout,
            batch_first=True,
            activation="gelu",
        )
        self.layers = nn.TransformerEncoder(encoder_layer, num_layers=config.diffusion_conditioning_layers)
        self.cond_gate = nn.Linear(config.d_model, config.d_model)

    def forward(self, x: torch.Tensor, cond: torch.Tensor) -> torch.Tensor:
        x = x + torch.tanh(self.cond_gate(cond))
        return self.layers(x)


class VocsMambaDiffusionForecaster(nn.Module):
    def __init__(self, input_dim: int, config: ModelConfig, pred_len: int):
        super().__init__()
        self.config = config
        self.pred_len = pred_len
        self.num_steps = config.diffusion_steps
        self.predict_delta_from_last = config.predict_delta_from_last
        self.clip_denoised = config.diffusion_clip_denoised

        if config.diffusion_objective != "eps":
            raise ValueError("Only diffusion_objective='eps' is supported currently.")

        self.conditioning = ConditioningStack(input_dim=input_dim, config=config)

        self.y_proj = nn.Linear(1, config.d_model)
        self.time_emb = SinusoidalTimeEmbedding(config.d_model)
        self.time_mlp = nn.Sequential(
            nn.Linear(config.d_model, config.d_model),
            nn.SiLU(),
            nn.Linear(config.d_model, config.d_model),
        )

        self.denoiser_type = config.diffusion_denoiser_type
        if self.denoiser_type == "resnet":
            self.denoise_layers = nn.ModuleList(
                [
                    ConditionalResBlock1D(
                        d_model=config.d_model,
                        cond_dim=config.d_model,
                        dropout=config.dropout,
                    )
                    for _ in range(config.diffusion_resnet_blocks)
                ]
            )
            self.transformer_denoiser = None
        elif self.denoiser_type == "transformer":
            self.denoise_layers = nn.ModuleList()
            self.transformer_denoiser = TransformerDenoiser(config)
        else:
            self.denoise_layers = nn.ModuleList([VocsMambaBlock(config) for _ in range(config.n_layer)])
            self.transformer_denoiser = None
        self.denoise_norm = nn.LayerNorm(config.d_model)
        self.eps_head = nn.Linear(config.d_model, 1)
        self.recon_head = nn.Linear(config.d_model, 1)
        self.recon_weight = max(0.0, float(config.diffusion_aux_recon_weight))
        self.seq_weight_stair_bins = max(1, int(config.diffusion_seq_weight_stair_bins))
        self.seq_weight_min = float(config.diffusion_seq_weight_min)
        self.seq_weight_max = float(config.diffusion_seq_weight_max)

        betas = torch.linspace(config.diffusion_beta_start, config.diffusion_beta_end, self.num_steps)
        alphas = 1.0 - betas
        alphas_cumprod = torch.cumprod(alphas, dim=0)
        alphas_cumprod_prev = torch.cat([torch.ones(1), alphas_cumprod[:-1]], dim=0)

        self.register_buffer("betas", betas)
        self.register_buffer("alphas", alphas)
        self.register_buffer("alphas_cumprod", alphas_cumprod)
        self.register_buffer("alphas_cumprod_prev", alphas_cumprod_prev)
        self.register_buffer("sqrt_alphas_cumprod", torch.sqrt(alphas_cumprod))
        self.register_buffer("sqrt_one_minus_alphas_cumprod", torch.sqrt(1.0 - alphas_cumprod))
        self.register_buffer("sqrt_recip_alphas", torch.sqrt(1.0 / alphas))
        posterior_variance = betas * (1.0 - alphas_cumprod_prev) / (1.0 - alphas_cumprod)
        self.register_buffer("posterior_variance", posterior_variance.clamp(min=1e-20))

        total_params = count_parameters(self)
        if total_params > config.max_parameters:
            raise ValueError(
                f"Model has {total_params:,} parameters, exceeding the 880M cap ({config.max_parameters:,})."
            )

    def _extract(self, values: torch.Tensor, timesteps: torch.Tensor, ref: torch.Tensor) -> torch.Tensor:
        out = values.gather(0, timesteps)
        return out.reshape(ref.shape[0], 1, 1)

    def _encode_condition(self, inputs: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        return self.conditioning(inputs, pred_len=self.pred_len)

    def _predict_eps(self, inputs: torch.Tensor, noisy_target: torch.Tensor, timesteps: torch.Tensor) -> torch.Tensor:
        cond, _ = self._encode_condition(inputs)
        noisy_proj = self.y_proj(noisy_target)
        t_emb = self.time_mlp(self.time_emb(timesteps)).unsqueeze(1)
        hidden_states = noisy_proj + cond + t_emb
        if self.transformer_denoiser is not None:
            hidden_states = self.transformer_denoiser(hidden_states, cond)
        elif self.denoiser_type == "resnet":
            for layer in self.denoise_layers:
                hidden_states = layer(hidden_states, cond)
        else:
            for layer in self.denoise_layers:
                hidden_states = layer(hidden_states)
        hidden_states = self.denoise_norm(hidden_states)
        return self.eps_head(hidden_states)

    def _predict_recon(self, inputs: torch.Tensor, noisy_target: torch.Tensor, timesteps: torch.Tensor) -> torch.Tensor:
        cond, _ = self._encode_condition(inputs)
        noisy_proj = self.y_proj(noisy_target)
        t_emb = self.time_mlp(self.time_emb(timesteps)).unsqueeze(1)
        hidden_states = noisy_proj + cond + t_emb
        if self.transformer_denoiser is not None:
            hidden_states = self.transformer_denoiser(hidden_states, cond)
        elif self.denoiser_type == "resnet":
            for layer in self.denoise_layers:
                hidden_states = layer(hidden_states, cond)
        else:
            for layer in self.denoise_layers:
                hidden_states = layer(hidden_states)
        hidden_states = self.denoise_norm(hidden_states)
        return self.recon_head(hidden_states)

    def q_sample(self, clean_target: torch.Tensor, timesteps: torch.Tensor, noise: torch.Tensor) -> torch.Tensor:
        sqrt_alpha = self._extract(self.sqrt_alphas_cumprod, timesteps, clean_target)
        sqrt_one_minus = self._extract(self.sqrt_one_minus_alphas_cumprod, timesteps, clean_target)
        return sqrt_alpha * clean_target + sqrt_one_minus * noise

    def forward(self, inputs: torch.Tensor, noisy_target: torch.Tensor, timesteps: torch.Tensor) -> torch.Tensor:
        return self._predict_eps(inputs, noisy_target, timesteps)

    def loss(self, inputs: torch.Tensor, clean_target: torch.Tensor) -> torch.Tensor:
        batch_size = inputs.shape[0]
        timesteps = torch.randint(0, self.num_steps, (batch_size,), device=inputs.device, dtype=torch.long)
        noise = torch.randn_like(clean_target)
        noisy_target = self.q_sample(clean_target, timesteps, noise)
        eps_pred = self._predict_eps(inputs, noisy_target, timesteps)
        eps_loss = torch.mean((noise - eps_pred) ** 2)
        if self.recon_weight <= 0.0:
            return eps_loss
        recon_pred = self._predict_recon(inputs, noisy_target, timesteps)
        # Stair-step weighting: larger diffusion timesteps receive higher sequence-error weight.
        recon_per_sample = torch.mean(torch.abs(recon_pred - clean_target), dim=(1, 2))
        t_den = max(1, self.num_steps - 1)
        t_ratio = timesteps.float() / float(t_den)
        stair_idx = torch.floor(t_ratio * self.seq_weight_stair_bins).long().clamp(max=self.seq_weight_stair_bins - 1)
        if self.seq_weight_stair_bins == 1:
            stair_alpha = torch.zeros_like(t_ratio)
        else:
            stair_alpha = stair_idx.float() / float(self.seq_weight_stair_bins - 1)
        stair_weight = self.seq_weight_min + (self.seq_weight_max - self.seq_weight_min) * stair_alpha
        recon_loss = torch.mean(stair_weight * recon_per_sample)
        return eps_loss + self.recon_weight * recon_loss

    @torch.inference_mode()
    def sample(self, inputs: torch.Tensor, num_steps: int | None = None) -> torch.Tensor:
        steps = self.num_steps if num_steps is None else max(1, min(num_steps, self.num_steps))
        batch_size = inputs.shape[0]
        generated = torch.randn(batch_size, self.pred_len, 1, device=inputs.device)

        for step in range(steps - 1, -1, -1):
            timesteps = torch.full((batch_size,), step, device=inputs.device, dtype=torch.long)
            eps_pred = self._predict_eps(inputs, generated, timesteps)

            alpha_t = self._extract(self.alphas, timesteps, generated)
            alpha_bar_t = self._extract(self.alphas_cumprod, timesteps, generated)
            sqrt_recip_alpha_t = self._extract(self.sqrt_recip_alphas, timesteps, generated)
            beta_t = self._extract(self.betas, timesteps, generated)
            posterior_var_t = self._extract(self.posterior_variance, timesteps, generated)

            mean = sqrt_recip_alpha_t * (generated - (beta_t / torch.sqrt(1.0 - alpha_bar_t)) * eps_pred)
            if step > 0:
                noise = torch.randn_like(generated)
                generated = mean + torch.sqrt(posterior_var_t) * noise
            else:
                generated = mean

        if self.predict_delta_from_last:
            last_target = inputs[:, -1:, -1:]
            generated = generated + last_target

        if self.clip_denoised:
            generated = generated.clamp(min=0.0)

        return generated


class DLinearForecaster(nn.Module):
    """
    DLinear: Pure linear forecasting model with trend-seasonal decomposition.
    
    Works by decomposing each input feature into trend and seasonal components,
    then applying separate linear transformations to each component.
    """

    def __init__(
        self,
        input_dim: int,
        config: ModelConfig,
        pred_len: int,
        decomp_kernel: int = 25,
        seq_len: int = 96,
        hidden_dims: tuple[int, ...] = (),
        branch_dropout: float = 0.0,
    ):
        super().__init__()
        self.input_dim = input_dim
        self.pred_len = pred_len
        self.seq_len = seq_len
        self.decomp_kernel = decomp_kernel
        self.hidden_dims = tuple(hidden_dims)
        self.branch_dropout = float(branch_dropout)
        
        # Moving average decomposition
        self.decomp = MovingAverageDecomp(kernel_size=decomp_kernel)
        
        self.trend_linear = self._build_projection(seq_len, pred_len)
        self.seasonal_linear = self._build_projection(seq_len, pred_len)

    def _build_projection(self, in_dim: int, out_dim: int) -> nn.Module:
        if not self.hidden_dims:
            return nn.Linear(in_dim, out_dim)

        layers: list[nn.Module] = []
        prev_dim = in_dim
        for hidden_dim in self.hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.GELU())
            if self.branch_dropout > 0.0:
                layers.append(nn.Dropout(self.branch_dropout))
            prev_dim = hidden_dim
        layers.append(nn.Linear(prev_dim, out_dim))
        return nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: [batch_size, seq_len, input_dim]
        
        Returns:
            [batch_size, pred_len, 1] (predicting only the target column)
        """
        batch_size = x.shape[0]
        
        # Extract target column (last column, typically rto_out_conc)
        target = x[:, :, -1:]  # [B, L, 1]
        
        # Decompose into seasonal and trend
        seasonal, trend = self.decomp(target)  # both [B, L, 1]
        
        # Apply linear projections
        # Reshape for linear layer: [B*1, L] -> [B*1, P]
        seasonal_proj = seasonal.squeeze(-1)  # [B, L]
        trend_proj = trend.squeeze(-1)        # [B, L]
        
        seasonal_fore = self.seasonal_linear(seasonal_proj).unsqueeze(-1)  # [B, P, 1]
        trend_fore = self.trend_linear(trend_proj).unsqueeze(-1)           # [B, P, 1]
        
        # Combine trend and seasonal forecasts
        output = seasonal_fore + trend_fore  # [B, P, 1]
        
        return output

    def loss(self, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        """
        Compute MSE loss between prediction and ground truth.
        
        Args:
            x: [batch_size, seq_len, input_dim]
            y: [batch_size, pred_len, 1]
        
        Returns:
            scalar loss
        """
        y_pred = self.forward(x)
        loss = F.mse_loss(y_pred, y)
        return loss

    def sample(self, x: torch.Tensor, num_steps: int | None = None) -> torch.Tensor:
        """
        Inference method - just returns the model's forward pass.
        DLinear is deterministic, so num_steps is ignored.
        
        Args:
            x: [batch_size, seq_len, input_dim]
            num_steps: ignored
        
        Returns:
            [batch_size, pred_len, 1]
        """
        return self.forward(x)


class DLinearForecasterLarge(DLinearForecaster):
    """
    Parameter-expanded DLinear variant with deeper trend/seasonal projection branches.
    """

    def __init__(
        self,
        input_dim: int,
        config: ModelConfig,
        pred_len: int,
        decomp_kernel: int = 25,
        seq_len: int = 96,
        hidden_dims: tuple[int, ...] = (256, 128),
        branch_dropout: float = 0.1,
    ):
        super().__init__(
            input_dim=input_dim,
            config=config,
            pred_len=pred_len,
            decomp_kernel=decomp_kernel,
            seq_len=seq_len,
            hidden_dims=hidden_dims,
            branch_dropout=branch_dropout,
        )


class DLinearMambaEncoder(nn.Module):
    """
    Hybrid forecaster: Mamba encoder for sequence representation + DLinear head.
    """

    def __init__(
        self,
        input_dim: int,
        config: ModelConfig,
        pred_len: int,
        decomp_kernel: int = 25,
        seq_len: int = 96,
        encoder_layers: int = 1,
    ):
        super().__init__()
        self.input_dim = input_dim
        self.pred_len = pred_len
        self.seq_len = seq_len
        self.decomp_kernel = decomp_kernel

        self.input_proj = nn.Sequential(
            nn.Linear(input_dim, config.d_model),
            nn.LayerNorm(config.d_model),
        )
        self.encoder = nn.ModuleList([VocsMambaBlock(config) for _ in range(max(1, int(encoder_layers)))])
        self.to_target = nn.Linear(config.d_model, 1)

        self.decomp = MovingAverageDecomp(kernel_size=decomp_kernel)
        self.trend_linear = nn.Linear(seq_len, pred_len)
        self.seasonal_linear = nn.Linear(seq_len, pred_len)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: [batch_size, seq_len, input_dim]

        Returns:
            [batch_size, pred_len, 1]
        """
        hidden_states = self.input_proj(x)
        for layer in self.encoder:
            hidden_states = layer(hidden_states)

        target_repr = self.to_target(hidden_states)
        seasonal, trend = self.decomp(target_repr)

        seasonal_proj = seasonal.squeeze(-1)
        trend_proj = trend.squeeze(-1)
        seasonal_fore = self.seasonal_linear(seasonal_proj).unsqueeze(-1)
        trend_fore = self.trend_linear(trend_proj).unsqueeze(-1)
        return seasonal_fore + trend_fore

    def loss(self, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        y_pred = self.forward(x)
        return F.mse_loss(y_pred, y)

    def sample(self, x: torch.Tensor, num_steps: int | None = None) -> torch.Tensor:
        return self.forward(x)
