import unittest
import sys
from pathlib import Path

import torch

project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
ensemble_docker_root = project_root / "ensemble_docker"
if str(ensemble_docker_root) not in sys.path:
    sys.path.insert(0, str(ensemble_docker_root))

from src.config import ModelConfig
from src.model import TransformerForecaster
from api_src.model import TransformerForecaster as ApiTransformerForecaster


class TestTransformerCompat(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(42)
        self.batch_size = 4
        self.seq_len = 96
        self.pred_len = 24
        self.input_dim = 51
        self.config = ModelConfig(d_model=128, ff_mult=2, dropout=0.1)

        self.x = torch.randn(self.batch_size, self.seq_len, self.input_dim)
        self.y = torch.randn(self.batch_size, self.pred_len, 1)

    def test_src_transformer_forward_shape(self):
        model = TransformerForecaster(
            input_dim=self.input_dim,
            config=self.config,
            pred_len=self.pred_len,
            seq_len=self.seq_len,
            n_heads=8,
            n_layers=2,
        )
        out = model(self.x)
        self.assertEqual(out.shape, (self.batch_size, self.pred_len, 1))

    def test_src_transformer_loss_and_sample(self):
        model = TransformerForecaster(
            input_dim=self.input_dim,
            config=self.config,
            pred_len=self.pred_len,
            seq_len=self.seq_len,
            n_heads=8,
            n_layers=2,
        )
        loss = model.loss(self.x, self.y)
        self.assertEqual(loss.dim(), 0)
        sampled = model.sample(self.x)
        self.assertEqual(sampled.shape, (self.batch_size, self.pred_len, 1))

    def test_api_transformer_forward_shape(self):
        model = ApiTransformerForecaster(
            input_dim=self.input_dim,
            config=self.config,
            pred_len=self.pred_len,
            seq_len=self.seq_len,
            n_heads=8,
            n_layers=2,
        )
        out = model(self.x)
        self.assertEqual(out.shape, (self.batch_size, self.pred_len, 1))

    def test_training_loop_contract(self):
        model = TransformerForecaster(
            input_dim=self.input_dim,
            config=self.config,
            pred_len=self.pred_len,
            seq_len=self.seq_len,
            n_heads=8,
            n_layers=2,
        )
        optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

        before = model.loss(self.x, self.y)
        optimizer.zero_grad(set_to_none=True)
        before.backward()
        optimizer.step()
        after = model.loss(self.x, self.y)

        self.assertTrue(torch.isfinite(before).item())
        self.assertTrue(torch.isfinite(after).item())


if __name__ == "__main__":
    unittest.main()
