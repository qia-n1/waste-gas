from dataclasses import dataclass
from pathlib import Path


SENSOR_COLUMNS = [
    "timestamp",
    "ambient_temp",
    "ambient_humidity",
    "ambient_pressure",
    "coating_flow",
    "coating_conc",
    "coating_temp",
    "coating_pressure",
    "rotor_speed",
    "adsorption_fan_power",
    "desorption_fan_power",
    "rotor_inlet_temp",
    "rotor_inlet_humid",
    "desorption_temp",
    "concentrated_flow",
    "concentrated_conc",
    "concentrated_temp",
    "concentrated_pressure",
    "rto_in_flow",
    "rto_in_conc",
    "rto_in_temp",
    "rto_in_pressure",
    "burner_gas_flow",
    "combustion_temp",
    "rto_out_conc",
    "rto_out_temp",
]

TARGET_COLUMN = "rto_out_conc"
ROLLING_WINDOWS = (6, 12, 24, 48, 96)
TIME_FEATURE_COLUMNS = (
    "hour_sin",
    "hour_cos",
    "weekday_sin",
    "weekday_cos",
    "month_sin",
    "month_cos",
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
VOCS_ROOT = PROJECT_ROOT.parent / "VOCS"


@dataclass
class DataConfig:
    seq_len: int = 96
    pred_len: int = 24
    train_ratio: float = 0.7
    val_ratio: float = 0.15
    exceed_threshold: float = 80.0
    exceed_sample_weight: float = 1.0
    dataset_csv: Path = VOCS_ROOT / "src" / "data" / "vocs_dataset.csv"
    realtime_csv: Path = PROJECT_ROOT / "data" / "vocs_realtime_data.csv"
    scaler_path: Path = PROJECT_ROOT / "artifacts" / "models" / "new_VOC_scalers.pkl"
    checkpoint_path: Path = PROJECT_ROOT / "artifacts" / "models" / "new_VOC_best.pt"


@dataclass
class ModelConfig:
    d_model: int = 768
    n_layer: int = 16
    d_state: int = 128
    expand: int = 2
    headdim: int = 64
    dropout: float = 0.10
    ff_mult: int = 2
    chunk_size: int = 64
    rope_fraction: float = 0.5
    is_mimo: bool = False
    residual_scale_mixer: float = 1.0
    residual_scale_ffn: float = 1.0
    use_multi_horizon_heads: bool = False
    short_horizon: int = 8
    medium_horizon: int = 8
    enable_exceed_aux_head: bool = False
    aux_head_hidden: int = 128
    predict_delta_from_last: bool = False
    diffusion_steps: int = 100
    diffusion_beta_start: float = 1e-4
    diffusion_beta_end: float = 2e-2
    diffusion_objective: str = "eps"
    diffusion_clip_denoised: bool = True
    diffusion_conditioning_type: str = "mamba"
    diffusion_conditioning_layers: int = 2
    diffusion_prob_sparse_topk: int = 16
    diffusion_temporal_embed_dim: int = 64
    diffusion_time_feature_indices: tuple[int, int, int, int] | tuple[()] = ()
    diffusion_use_weekend_gate: bool = True
    diffusion_denoiser_type: str = "mamba"
    diffusion_resnet_blocks: int = 4
    diffusion_aux_recon_weight: float = 0.0
    diffusion_seq_weight_stair_bins: int = 4
    diffusion_seq_weight_min: float = 0.05
    diffusion_seq_weight_max: float = 0.30
    max_parameters: int = 880_000_000


@dataclass
class TrainConfig:
    batch_size: int = 32
    epochs: int = 50
    learning_rate: float = 3e-4
    weight_decay: float = 1e-4
    grad_clip: float = 1.0
    early_stop_patience: int = 10
    seed: int = 42
    output_dir: Path = PROJECT_ROOT / "artifacts"
