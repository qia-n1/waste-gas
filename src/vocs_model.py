import os
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
from datetime import datetime
import pickle

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error


class Config:
    DATA_PATH = "src/data/vocs_dataset.csv"
    OUTPUT_DIR = None

    SEQ_LEN = 96
    PRED_LEN = 24
    HIDDEN_DIM = 256
    NUM_LAYERS = 3
    DROPOUT = 0.3
    TEACHER_FORCING_START = 0.5
    TEACHER_FORCING_END = 0.05
    TEACHER_FORCING_DECAY = 0.98

    BATCH_SIZE = 64
    LEARNING_RATE = 0.0008
    WEIGHT_DECAY = 1e-5
    EPOCHS = 150
    EARLY_STOP_PATIENCE = 20
    GRAD_CLIP = 1.0

    LOSS_WEIGHTS = {
        'short': 3.0,
        'medium': 2.0,
        'long': 1.0
    }

    TRAIN_RATIO = 0.7
    VAL_RATIO = 0.15
    SEED = 42

    # 优化参数（统一管理）
    EXCEED_THRESHOLD = 80  # VOCs超标阈值
    EXCEED_SAMPLE_WEIGHT = 5.0  # 超标样本权重
    POSITION_NORMALIZATION = 24.0  # 位置偏置归一化因子

    def __init__(self):
        if self.OUTPUT_DIR is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.OUTPUT_DIR = os.path.join("src", "outputs", timestamp)

        self.MODEL_DIR = os.path.join(self.OUTPUT_DIR, "models")
        self.LOG_DIR = os.path.join(self.OUTPUT_DIR, "logs")

        os.makedirs(self.OUTPUT_DIR, exist_ok=True)
        os.makedirs(self.MODEL_DIR, exist_ok=True)
        os.makedirs(self.LOG_DIR, exist_ok=True)


config = Config()
torch.manual_seed(config.SEED)
np.random.seed(config.SEED)


class VOCsDataProcessor:
    def __init__(self, config):
        self.config = config
        self.feature_scaler = MinMaxScaler()
        self.target_scaler = MinMaxScaler()

    def add_time_features(self, df):
        df = df.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        df['hour_sin'] = np.sin(2 * np.pi * df['timestamp'].dt.hour / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['timestamp'].dt.hour / 24)
        df['weekday_sin'] = np.sin(2 * np.pi * df['timestamp'].dt.weekday / 7)
        df['weekday_cos'] = np.cos(2 * np.pi * df['timestamp'].dt.weekday / 7)
        df['month_sin'] = np.sin(2 * np.pi * df['timestamp'].dt.month / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['timestamp'].dt.month / 12)

        return df

    def add_rolling_features(self, df):
        df = df.copy()
        target_col = 'rto_out_conc'
        windows = [6, 12, 24, 48, 96]

        for window in windows:
            df[f'{target_col}_rolling_mean_{window}'] = df[target_col].rolling(window=window, min_periods=1).mean()
            df[f'{target_col}_rolling_std_{window}'] = df[target_col].rolling(window=window, min_periods=1).std().fillna(0)
            df[f'{target_col}_rolling_trend_{window}'] = df[target_col].rolling(window=window).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) >= 2 else 0
            ).fillna(0)

        df[f'{target_col}_diff_1'] = df[target_col].diff(1).fillna(0)
        df[f'{target_col}_diff_4'] = df[target_col].diff(4).fillna(0)
        df[f'{target_col}_diff_24'] = df[target_col].diff(24).fillna(0)
        df[f'{target_col}_diff_96'] = df[target_col].diff(96).fillna(0)
        df[f'{target_col}_ma_diff_24'] = df[target_col] - df[f'{target_col}_rolling_mean_24']

        return df

    def augment_exceed_samples(self, df):
        target_col = 'rto_out_conc'
        exceed_mask = df[target_col] > self.config.EXCEED_THRESHOLD
        exceed_samples = df[exceed_mask].copy()

        if len(exceed_samples) > 0:
            noise = np.random.normal(0, 1, exceed_samples.shape[0])
            exceed_samples_aug = exceed_samples.copy()
            exceed_samples_aug[target_col] += noise
            df_augmented = pd.concat([df, exceed_samples_aug], ignore_index=True)
            return df_augmented
        return df

    def create_sequences(self, df):
        exclude_cols = ['timestamp', 'rto_out_conc']
        feature_columns = [col for col in df.columns if col not in exclude_cols]

        X = df[feature_columns].values
        y = df['rto_out_conc'].values.reshape(-1, 1)

        X_scaled = self.feature_scaler.fit_transform(X)
        y_scaled = self.target_scaler.fit_transform(y)

        Xs, ys = [], []
        total_len = len(X_scaled)

        for i in range(total_len - self.config.SEQ_LEN - self.config.PRED_LEN + 1):
            X_seq = X_scaled[i : i + self.config.SEQ_LEN]
            y_seq = y_scaled[i + self.config.SEQ_LEN : i + self.config.SEQ_LEN + self.config.PRED_LEN]
            hist_target = y_scaled[i : i + self.config.SEQ_LEN]
            X_with_hist = np.concatenate([X_seq, hist_target], axis=1)

            Xs.append(X_with_hist)
            ys.append(y_seq)

        return np.array(Xs), np.array(ys)

    def split_data(self, X, y):
        n = len(X)
        train_end = int(n * self.config.TRAIN_RATIO)
        val_end = int(n * (self.config.TRAIN_RATIO + self.config.VAL_RATIO))

        return (X[:train_end], y[:train_end]), (X[train_end:val_end], y[train_end:val_end]), (X[val_end:], y[val_end:])

    def process(self, df):
        df = self.add_time_features(df)
        df = self.add_rolling_features(df)
        df = self.augment_exceed_samples(df)
        X, y = self.create_sequences(df)
        return self.split_data(X, y)

    def save_scalers(self, scaler_path: str, df=None):
        try:
            if df is not None and 'timestamp' in df.columns:
                df_with_features = df.copy()
                df_with_features = self.add_time_features(df_with_features)
                df_with_features = self.add_rolling_features(df_with_features)
                exclude_cols = ['timestamp', 'rto_out_conc']
                feature_columns = [col for col in df_with_features.columns if col not in exclude_cols]
            else:
                feature_columns = [
                    'hour_sin', 'hour_cos',
                    'weekday_sin', 'weekday_cos',
                    'month_sin', 'month_cos',
                    'rto_out_conc_rolling_mean_6', 'rto_out_conc_rolling_std_6', 'rto_out_conc_rolling_trend_6',
                    'rto_out_conc_rolling_mean_12', 'rto_out_conc_rolling_std_12', 'rto_out_conc_rolling_trend_12',
                    'rto_out_conc_rolling_mean_24', 'rto_out_conc_rolling_std_24', 'rto_out_conc_rolling_trend_24',
                    'rto_out_conc_rolling_mean_48', 'rto_out_conc_rolling_std_48', 'rto_out_conc_rolling_trend_48',
                    'rto_out_conc_rolling_mean_96', 'rto_out_conc_rolling_std_96', 'rto_out_conc_rolling_trend_96',
                    'rto_out_conc_diff_1', 'rto_out_conc_diff_4',
                    'rto_out_conc_diff_24', 'rto_out_conc_diff_96',
                    'rto_out_conc_ma_diff_24'
                ]

            scaler_data = {
                'feature_scaler': self.feature_scaler,
                'target_scaler': self.target_scaler,
                'feature_columns': feature_columns,
                'input_dim': len(feature_columns) + 1,
                'save_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            with open(scaler_path, 'wb') as f:
                pickle.dump(scaler_data, f)

            return True
        except Exception as e:
            print(f"保存Scaler失败: {e}")
            return False


class ImprovedAttentionLayer(nn.Module):
    def __init__(self, hidden_dim):
        super().__init__()
        self.attention = nn.Linear(hidden_dim * 2, hidden_dim)
        self.v = nn.Linear(hidden_dim, 1, bias=False)
        self.position_bias = nn.Parameter(torch.randn(1, 1, hidden_dim))

    def forward(self, encoder_outputs, decoder_hidden, step=None, position_norm=24.0):
        batch_size, seq_len, _ = encoder_outputs.shape
        decoder_hidden = decoder_hidden.unsqueeze(1).repeat(1, seq_len, 1)

        concat = torch.cat((encoder_outputs, decoder_hidden), dim=2)
        energy = torch.tanh(self.attention(concat))

        if step is not None:
            position_weight = step / position_norm
            energy = energy + self.position_bias * position_weight

        attention_scores = self.v(energy).squeeze(2)
        attention_weights = nn.functional.softmax(attention_scores, dim=1)
        context = torch.bmm(attention_weights.unsqueeze(1), encoder_outputs).squeeze(1)

        return context, attention_weights


class ImprovedSeq2SeqModel(nn.Module):
    def __init__(self, config, input_dim):
        super().__init__()
        self.config = config

        self.encoder = nn.LSTM(
            input_size=input_dim,
            hidden_size=config.HIDDEN_DIM,
            num_layers=config.NUM_LAYERS,
            batch_first=True,
            dropout=config.DROPOUT if config.NUM_LAYERS > 1 else 0
        )

        self.decoder = nn.LSTM(
            input_size=1 + config.HIDDEN_DIM,
            hidden_size=config.HIDDEN_DIM,
            num_layers=config.NUM_LAYERS,
            batch_first=True,
            dropout=config.DROPOUT if config.NUM_LAYERS > 1 else 0
        )

        self.attention = ImprovedAttentionLayer(config.HIDDEN_DIM)
        self.fc_out = nn.Linear(config.HIDDEN_DIM, 1)
        self.gate = nn.Linear(config.HIDDEN_DIM * 2, config.HIDDEN_DIM)

    def forward(self, src, target=None, teacher_forcing_ratio=0.5):
        encoder_outputs, (hidden, cell) = self.encoder(src)
        decoder_input = src[:, -1:, -1:]
        outputs = []

        use_teacher_forcing = False
        if target is not None and self.training and np.random.random() < teacher_forcing_ratio:
            use_teacher_forcing = True

        for t in range(self.config.PRED_LEN):
            context, _ = self.attention(
                encoder_outputs,
                hidden[-1],
                step=t,
                position_norm=self.config.POSITION_NORMALIZATION
            )

            decoder_input_concat = torch.cat((decoder_input, context.unsqueeze(1)), dim=2)
            decoder_output, (hidden, cell) = self.decoder(decoder_input_concat, (hidden, cell))

            prediction = self.fc_out(decoder_output)

            gate = torch.sigmoid(self.gate(torch.cat([decoder_output, context.unsqueeze(1)], dim=2)))
            decoder_output = gate * decoder_output + (1 - gate) * context.unsqueeze(1)

            outputs.append(prediction)

            if use_teacher_forcing:
                decoder_input = target[:, t:t+1, :]
            else:
                decoder_input = prediction

        outputs = torch.cat(outputs, dim=1)
        return outputs


class MultiStageWeightedLoss(nn.Module):
    def __init__(self, target_scaler, loss_weights, exceed_threshold=80, exceed_weight=5.0):
        super().__init__()
        self.target_scaler = target_scaler
        self.loss_weights = loss_weights
        self.exceed_threshold = exceed_threshold
        self.exceed_weight = exceed_weight

    def forward(self, predictions, targets):
        pred_len, _ = targets.shape[1], targets.shape[2]
        weights = torch.ones_like(targets)

        short_end = min(8, pred_len)
        weights[:, :short_end, :] *= self.loss_weights['short']

        medium_start = short_end
        medium_end = min(16, pred_len)
        weights[:, medium_start:medium_end, :] *= self.loss_weights['medium']

        long_start = medium_end
        weights[:, long_start:, :] *= self.loss_weights['long']

        targets_np = targets.detach().cpu().numpy().reshape(-1, 1)
        targets_original = self.target_scaler.inverse_transform(targets_np).reshape(targets.shape)
        exceed_mask = torch.tensor(targets_original > self.exceed_threshold, dtype=torch.float32).to(targets.device)
        weights = weights + exceed_mask.unsqueeze(1) * self.exceed_weight

        weighted_loss = weights * (predictions - targets) ** 2
        return weighted_loss.mean()


class ImprovedTrainer:
    def __init__(self, model, config, processor):
        self.model = model
        self.config = config
        self.processor = processor
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        self.log_file_path = os.path.join(config.LOG_DIR, "training.log")
        self._init_log_file()

        self.model.to(self.device)

        self.optimizer = optim.Adam(
            self.model.parameters(),
            lr=config.LEARNING_RATE,
            weight_decay=config.WEIGHT_DECAY
        )

        self.scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode='min', factor=0.5, patience=10
        )

        self.criterion = MultiStageWeightedLoss(
            processor.target_scaler,
            config.LOSS_WEIGHTS,
            exceed_threshold=config.EXCEED_THRESHOLD,
            exceed_weight=config.EXCEED_SAMPLE_WEIGHT
        )

        self.current_teacher_forcing = config.TEACHER_FORCING_START

        self.history = {
            'train_loss': [],
            'val_loss': [],
            'val_r2': [],
            'trend_acc': [],
            'exceed_acc': [],
            'teacher_forcing': []
        }

        self.best_val_loss = float('inf')
        self.patience_counter = 0

    def _init_log_file(self):
        with open(self.log_file_path, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write(" " * 15 + "VOCs模型训练日志\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"训练开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"设备: {self.device}\n")
            f.write(f"模型参数: {sum(p.numel() for p in self.model.parameters()):,}\n")
            f.write(f"损失权重: 短期x{self.config.LOSS_WEIGHTS['short']}, "
                   f"中期x{self.config.LOSS_WEIGHTS['medium']}, "
                   f"长期x{self.config.LOSS_WEIGHTS['long']}\n")
            f.write(f"Scheduled Sampling: {self.config.TEACHER_FORCING_START} → {self.config.TEACHER_FORCING_END}\n")
            f.write("=" * 70 + "\n\n\n")

    def _log(self, message):
        print(message)
        with open(self.log_file_path, 'a', encoding='utf-8') as f:
            f.write(message + "\n")

    def train_epoch(self, train_loader):
        self.model.train()
        total_loss = 0

        for X_batch, y_batch in train_loader:
            X_batch = X_batch.to(self.device)
            y_batch = y_batch.to(self.device)

            predictions = self.model(X_batch, y_batch, teacher_forcing_ratio=self.current_teacher_forcing)
            loss = self.criterion(predictions, y_batch)

            self.optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.config.GRAD_CLIP)
            self.optimizer.step()

            total_loss += loss.item()

        return total_loss / len(train_loader)

    def validate(self, val_loader):
        self.model.eval()
        total_loss = 0
        all_preds = []
        all_targets = []

        with torch.no_grad():
            for X_batch, y_batch in val_loader:
                X_batch = X_batch.to(self.device)
                y_batch = y_batch.to(self.device)

                predictions = self.model(X_batch)
                loss = self.criterion(predictions, y_batch)

                total_loss += loss.item()
                all_preds.append(predictions.cpu().numpy())
                all_targets.append(y_batch.cpu().numpy())

        all_preds = np.concatenate(all_preds, axis=0)
        all_targets = np.concatenate(all_targets, axis=0)

        r2_scores = []
        for t in range(self.config.PRED_LEN):
            r2 = r2_score(all_targets[:, t, 0], all_preds[:, t, 0])
            r2_scores.append(r2)

        avg_r2 = np.mean(r2_scores)
        trend_accuracy = self._calculate_trend_accuracy(all_targets, all_preds)
        exceed_accuracy = self._calculate_exceed_accuracy(all_targets, all_preds)

        return total_loss / len(val_loader), avg_r2, trend_accuracy, exceed_accuracy

    def _calculate_trend_accuracy(self, targets, preds):
        target_trend = targets[:, -1, 0] - targets[:, 0, 0]
        pred_trend = preds[:, -1, 0] - preds[:, 0, 0]
        target_direction = (target_trend > 0).astype(int)
        pred_direction = (pred_trend > 0).astype(int)
        return (target_direction == pred_direction).mean()

    def _calculate_exceed_accuracy(self, targets, preds):
        targets_orig = self.processor.target_scaler.inverse_transform(
            targets.reshape(-1, 1)
        ).reshape(targets.shape)
        preds_orig = self.processor.target_scaler.inverse_transform(
            preds.reshape(-1, 1)
        ).reshape(preds.shape)
        target_exceed = (targets_orig > self.config.EXCEED_THRESHOLD).astype(int)
        pred_exceed = (preds_orig > self.config.EXCEED_THRESHOLD).astype(int)
        return (target_exceed == pred_exceed).mean()

    def train(self, train_loader, val_loader):
        self._log("=" * 70)
        self._log("开始训练...")
        self._log(f"设备: {self.device}")
        self._log(f"损失权重: 短期x{self.config.LOSS_WEIGHTS['short']}, "
                 f"中期x{self.config.LOSS_WEIGHTS['medium']}, 长期x{self.config.LOSS_WEIGHTS['long']}")
        self._log(f" Scheduled Sampling: {self.config.TEACHER_FORCING_START} → {self.config.TEACHER_FORCING_END}")
        self._log("=" * 70)

        for epoch in range(1, self.config.EPOCHS + 1):
            train_loss = self.train_epoch(train_loader)
            val_loss, val_r2, trend_accuracy, exceed_accuracy = self.validate(val_loader)

            self.scheduler.step(val_loss)

            self.current_teacher_forcing = max(
                self.config.TEACHER_FORCING_END,
                self.current_teacher_forcing * self.config.TEACHER_FORCING_DECAY
            )

            self.history['train_loss'].append(train_loss)
            self.history['val_loss'].append(val_loss)
            self.history['val_r2'].append(val_r2)
            self.history['trend_acc'].append(trend_accuracy)
            self.history['exceed_acc'].append(exceed_accuracy)
            self.history['teacher_forcing'].append(self.current_teacher_forcing)

            if epoch % 5 == 0 or epoch == 1:
                current_lr = self.optimizer.param_groups[0]['lr']
                self._log(f"Epoch {epoch:03d}/{self.config.EPOCHS} | "
                         f"Loss: {train_loss:.6f}/{val_loss:.6f} | "
                         f"R²: {val_r2:.4f} | "
                         f"趋势: {trend_accuracy:.1%} | "
                         f"超标: {exceed_accuracy:.1%} | "
                         f"TF: {self.current_teacher_forcing:.2f} | "
                         f"LR: {current_lr:.6f}")

            if val_loss < self.best_val_loss:
                self.best_val_loss = val_loss
                self.patience_counter = 0
                self.save_model(epoch, val_r2, trend_accuracy, exceed_accuracy, is_best=True)
                self._log(f"  最佳模型已保存 (Epoch {epoch}, R²={val_r2:.4f})")
            else:
                self.patience_counter += 1

            if self.patience_counter >= self.config.EARLY_STOP_PATIENCE:
                self._log(f"\n早停触发 (Epoch {epoch})")
                break

        self._log("=" * 70)
        self._log("训练完成！")
        self._log(f"最佳验证Loss: {self.best_val_loss:.6f}")
        self._log(f"训练结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self._log("=" * 70)

        return self.history

    def save_model(self, epoch, r2, trend_acc, exceed_acc, is_best=False):
        if is_best:
            path = os.path.join(self.config.MODEL_DIR, "vocs_seq2seq_v2_best.pth")
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(self.config.MODEL_DIR, f"vocs_seq2seq_v2_epoch{epoch}_{timestamp}.pth")

        torch.save({
            'epoch': epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'val_loss': self.best_val_loss if is_best else self.history['val_loss'][-1],
            'val_r2': r2,
            'trend_accuracy': trend_acc,
            'exceed_accuracy': exceed_acc,
            'teacher_forcing': self.current_teacher_forcing
        }, path)

    def save_logs(self):
        self._log(f"训练日志已保存: {self.log_file_path}")


def evaluate_model(model, test_loader, processor, config):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.eval()

    all_preds = []
    all_targets = []

    with torch.no_grad():
        for X_batch, y_batch in test_loader:
            X_batch = X_batch.to(device)
            predictions = model(X_batch)

            all_preds.append(predictions.cpu().numpy())
            all_targets.append(y_batch.numpy())

    all_preds = np.concatenate(all_preds, axis=0)
    all_targets = np.concatenate(all_targets, axis=0)

    print(f"\n分步预测性能 (未来6小时, 共{config.PRED_LEN}步):")
    print("-" * 80)
    print(f"{'步数':<6} {'时间':<10} {'R²':<10} {'MAE':<10} {'RMSE':<10}")
    print("-" * 80)

    metrics = []
    for t in range(config.PRED_LEN):
        pred_t = all_preds[:, t, 0]
        target_t = all_targets[:, t, 0]

        r2 = r2_score(target_t, pred_t)
        mae = mean_absolute_error(target_t, pred_t)
        rmse = np.sqrt(mean_squared_error(target_t, pred_t))

        time_label = f"+{(t+1)*15}min"
        print(f"{t+1:<6} {time_label:<10} {r2:<10.4f} {mae:<10.4f} {rmse:<10.4f}")
        metrics.append({'step': t+1, 'time': time_label, 'r2': r2, 'mae': mae, 'rmse': rmse})

    avg_r2 = np.mean([m['r2'] for m in metrics])
    avg_mae = np.mean([m['mae'] for m in metrics])
    avg_rmse = np.mean([m['rmse'] for m in metrics])

    print("-" * 80)
    print(f"{'平均':<6} {'':<10} {avg_r2:<10.4f} {avg_mae:<10.4f} {avg_rmse:<10.4f}")

    target_trend = all_targets[:, -1, 0] - all_targets[:, 0, 0]
    pred_trend = all_preds[:, -1, 0] - all_preds[:, 0, 0]
    target_direction = (target_trend > 0).astype(int)
    pred_direction = (pred_trend > 0).astype(int)
    trend_acc = (target_direction == pred_direction).mean()
    print(f"\n6小时趋势方向准确率: {trend_acc:.1%}")

    targets_orig = processor.target_scaler.inverse_transform(
        all_targets.reshape(-1, 1)
    ).reshape(all_targets.shape)
    preds_orig = processor.target_scaler.inverse_transform(
        all_preds.reshape(-1, 1)
    ).reshape(all_preds.shape)
    target_exceed = (targets_orig > config.EXCEED_THRESHOLD).astype(int)
    pred_exceed = (preds_orig > config.EXCEED_THRESHOLD).astype(int)
    exceed_acc = (target_exceed == pred_exceed).mean()
    print(f"超标预测准确率: {exceed_acc:.1%}")

    print(f"\n分阶段性能统计:")
    short_r2 = np.mean([m['r2'] for m in metrics[:8]])
    medium_r2 = np.mean([m['r2'] for m in metrics[8:16]])
    long_r2 = np.mean([m['r2'] for m in metrics[16:]])
    print(f"  短期（2小时）: R² = {short_r2:.4f}")
    print(f"  中期（4小时）: R² = {medium_r2:.4f}")
    print(f"  长期（6小时）: R² = {long_r2:.4f}")

    print(f"\n目标达成率: {avg_r2 * 100:.1f}% (目标: >80%)")

    if avg_r2 >= 0.8:
        print("模型达到预期性能")
    elif avg_r2 >= 0.7:
        print(f"良好，当前R²={avg_r2:.4f}")
    else:
        print(f"未达标，当前R²={avg_r2:.4f}")

    return all_preds, all_targets, metrics


def main():
    print("\n" + "="*70)
    print(" " * 20 + "VOCs时序预测模型")
    print("="*70 + "\n")

    df = pd.read_csv(config.DATA_PATH)
    print(f"数据加载完成: {df.shape}")

    processor = VOCsDataProcessor(config)
    (X_train, y_train), (X_val, y_val), (X_test, y_test) = processor.process(df)

    print(f"输入形状: {X_train.shape}, 输出形状: {y_train.shape}\n")

    train_dataset = TensorDataset(torch.FloatTensor(X_train), torch.FloatTensor(y_train))
    val_dataset = TensorDataset(torch.FloatTensor(X_val), torch.FloatTensor(y_val))
    test_dataset = TensorDataset(torch.FloatTensor(X_test), torch.FloatTensor(y_test))

    train_loader = DataLoader(train_dataset, batch_size=config.BATCH_SIZE, shuffle=False, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=config.BATCH_SIZE, shuffle=False, num_workers=0)
    test_loader = DataLoader(test_dataset, batch_size=config.BATCH_SIZE, shuffle=False, num_workers=0)

    input_dim = X_train.shape[2]
    model = ImprovedSeq2SeqModel(config, input_dim)

    print("模型架构:")
    print(f"  类型: Seq2Seq + Attention + Gate")
    print(f"  输入维度: {input_dim}")
    print(f"  历史窗口: {config.SEQ_LEN}步 ({config.SEQ_LEN//4}小时)")
    print(f"  预测窗口: {config.PRED_LEN}步 ({config.PRED_LEN//4}小时)")
    print(f"  隐藏层: {config.HIDDEN_DIM}维 × {config.NUM_LAYERS}层")
    print(f"  Dropout: {config.DROPOUT}")
    print(f"  参数量: {sum(p.numel() for p in model.parameters()):,}\n")

    trainer = ImprovedTrainer(model, config, processor)
    history = trainer.train(train_loader, val_loader)

    trainer.save_logs()

    model_path = os.path.join(config.MODEL_DIR, "vocs_seq2seq_v2_best.pth")
    print(f"\n加载最佳模型: {model_path}")
    checkpoint = torch.load(model_path, map_location='cpu', weights_only=False)
    model.load_state_dict(checkpoint['model_state_dict'])

    evaluate_model(model, test_loader, processor, config)

    scaler_path = os.path.join(config.MODEL_DIR, "vocs_scalers_v2.pkl")
    processor.save_scalers(scaler_path, df=df)

    print("\n" + "="*70)
    print(" " * 25 + "训练完成")
    print("="*70)
    print(f"输出目录: {config.OUTPUT_DIR}")
    print(f"模型文件: {config.MODEL_DIR}/")
    print(f"日志文件: {config.LOG_DIR}/")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
