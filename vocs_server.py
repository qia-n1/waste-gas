import os
import json
import logging
import asyncio
import numpy as np
import pandas as pd
import pickle
import torch
import torch.nn as nn
import torch.nn.functional as F
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
import uvicorn
from sklearn.preprocessing import MinMaxScaler

LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


def get_local_timestamp() -> str:
    """获取本地时间戳（确保使用系统本地时区，而不是UTC）"""
    # 获取当前时间并附加本地时区信息
    now = datetime.now().astimezone()
    return now.isoformat()


class AttentionLayer(nn.Module):
    def __init__(self, hidden_dim):
        super().__init__()
        self.attention = nn.Linear(hidden_dim * 2, hidden_dim)
        self.v = nn.Linear(hidden_dim, 1, bias=False)

    def forward(self, encoder_outputs, decoder_hidden):
        batch_size, seq_len, _ = encoder_outputs.shape
        decoder_hidden = decoder_hidden.unsqueeze(1).repeat(1, seq_len, 1)
        concat = torch.cat((encoder_outputs, decoder_hidden), dim=2)
        energy = torch.tanh(self.attention(concat))
        attention_scores = self.v(energy).squeeze(2)
        attention_weights = nn.functional.softmax(attention_scores, dim=1)
        context = torch.bmm(attention_weights.unsqueeze(1), encoder_outputs).squeeze(1)
        return context, attention_weights


class ImprovedAttentionLayer(nn.Module):
    def __init__(self, hidden_dim):
        super().__init__()
        self.attention = nn.Linear(hidden_dim * 2, hidden_dim)
        self.v = nn.Linear(hidden_dim, 1, bias=False)
        self.position_bias = nn.Parameter(torch.randn(1, 1, hidden_dim))

    def forward(self, encoder_outputs, decoder_hidden, step=None):
        batch_size, seq_len, _ = encoder_outputs.shape
        decoder_hidden = decoder_hidden.unsqueeze(1).repeat(1, seq_len, 1)
        concat = torch.cat((encoder_outputs, decoder_hidden), dim=2)
        energy = torch.tanh(self.attention(concat))
        if step is not None:
            position_weight = step / 24.0
            energy = energy + self.position_bias * position_weight
        attention_scores = self.v(energy).squeeze(2)
        attention_weights = nn.functional.softmax(attention_scores, dim=1)
        context = torch.bmm(attention_weights.unsqueeze(1), encoder_outputs).squeeze(1)
        return context, attention_weights


class Seq2SeqModel(nn.Module):
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
        self.attention = AttentionLayer(config.HIDDEN_DIM)
        self.fc_out = nn.Linear(config.HIDDEN_DIM, 1)

    def forward(self, src, target=None):
        batch_size = src.size(0)
        encoder_outputs, (hidden, cell) = self.encoder(src)
        decoder_input = src[:, -1:, -1:]
        outputs = []

        for t in range(self.config.PRED_LEN):
            context, _ = self.attention(encoder_outputs, hidden[-1])
            decoder_input_concat = torch.cat((decoder_input, context.unsqueeze(1)), dim=2)
            decoder_output, (hidden, cell) = self.decoder(decoder_input_concat, (hidden, cell))
            prediction = self.fc_out(decoder_output)
            outputs.append(prediction)
            hist_mean = src[:, -1:, -15:-14]
            decoder_input = 0.8 * prediction + 0.2 * hist_mean

        outputs = torch.cat(outputs, dim=1)
        return outputs


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
        batch_size = src.size(0)
        encoder_outputs, (hidden, cell) = self.encoder(src)
        decoder_input = src[:, -1:, -1:]
        outputs = []

        for t in range(self.config.PRED_LEN):
            context, _ = self.attention(encoder_outputs, hidden[-1], step=t)
            decoder_input_concat = torch.cat((decoder_input, context.unsqueeze(1)), dim=2)
            decoder_output, (hidden, cell) = self.decoder(decoder_input_concat, (hidden, cell))
            prediction = self.fc_out(decoder_output)
            gate = torch.sigmoid(self.gate(torch.cat([decoder_output, context.unsqueeze(1)], dim=2)))
            decoder_output = gate * decoder_output + (1 - gate) * context.unsqueeze(1)
            outputs.append(prediction)
            decoder_input = prediction

        outputs = torch.cat(outputs, dim=1)
        return outputs


class Seq2SeqConfig:
    SEQ_LEN = 48
    PRED_LEN = 24
    HIDDEN_DIM = 128
    NUM_LAYERS = 2
    DROPOUT = 0.3
    TEACHER_FORCING_RATIO = 0.3


class Seq2SeqV2Config:
    SEQ_LEN = 96
    PRED_LEN = 24
    HIDDEN_DIM = 256
    NUM_LAYERS = 3
    DROPOUT = 0.3
    TEACHER_FORCING_RATIO = 0.3


class SensorData(BaseModel):
    timestamp: str
    ambient_temp: float = 0.0
    ambient_humidity: float = 0.0
    ambient_pressure: float = 0.0
    coating_flow: float = 0.0
    coating_conc: float = 0.0
    coating_temp: float = 0.0
    coating_pressure: float = 0.0
    rotor_speed: float = 0.0
    adsorption_fan_power: float = 0.0
    desorption_fan_power: float = 0.0
    rotor_inlet_temp: float = 0.0
    rotor_inlet_humid: float = 0.0
    desorption_temp: float = 0.0
    concentrated_flow: float = 0.0
    concentrated_conc: float = 0.0
    concentrated_temp: float = 0.0
    concentrated_pressure: float = 0.0
    rto_in_flow: float = 0.0
    rto_in_temp: float = 0.0
    rto_in_pressure: float = 0.0
    burner_gas_flow: float = 0.0
    combustion_temp: float = 0.0
    rto_in_conc: float = 0.0
    rto_out_conc: float = 0.0
    rto_out_temp: float = 0.0


class PredictionResult(BaseModel):
    timestamp: str
    prediction_horizon: int
    predicted_values: List[float]
    confidence: float
    alert_triggered: bool
    alert_message: str
    prediction_type: str


class Alert(BaseModel):
    alert_id: str
    timestamp: str
    level: str
    message: str
    value: float
    threshold: float
    acknowledged: bool

class VOCsSystemManager:
    def __init__(self):
        self.model = None
        self.sensor_data_buffer: List[SensorData] = []
        self.predictions: List[PredictionResult] = []
        self.alerts: List[Alert] = []
        self.latest_prediction: Optional[PredictionResult] = None
        self.BUFFER_SIZE = 96
        self.PREDICTION_INTERVAL = 1
        self.PREDICTION_HORIZON = 24
        self.ALERT_THRESHOLD = 80.0
        self.DATA_COLLECTION_INTERVAL = 15
        self.MIN_DATA_FOR_PREDICTION = 96
        self.CSV_FILE_PATH = os.getenv("CSV_PATH", "vocs_realtime_data/vocs_realtime_data.csv")
        self.SCALER_FILE_PATH = os.getenv("SCALER_PATH", "models/vocs_scalers_v2.pkl")
        self.MODEL_PATH = os.getenv("MODEL_PATH", "models/vocs_seq2seq_v2_best.pth")
        self.total_data_received = 0
        self.total_predictions = 0
        self.total_alerts = 0
        self.system_start_time = datetime.now()
        self.dataset_fields = [
            'timestamp',
            'ambient_temp', 'ambient_humidity', 'ambient_pressure',
            'coating_flow', 'coating_conc', 'coating_temp', 'coating_pressure',
            'rotor_speed', 'adsorption_fan_power', 'desorption_fan_power',
            'rotor_inlet_temp', 'rotor_inlet_humid',
            'desorption_temp', 'concentrated_flow', 'concentrated_conc',
            'concentrated_temp', 'concentrated_pressure',
            'rto_in_flow', 'rto_in_temp', 'rto_in_pressure',
            'burner_gas_flow', 'combustion_temp',
            'rto_in_conc', 'rto_out_conc', 'rto_out_temp'
        ]
        self.feature_scaler = MinMaxScaler()
        self.target_scaler = MinMaxScaler()
        self._load_scalers()

        # 显示时区信息
        local_tz = datetime.now().astimezone().tzinfo
        logger.info(f"System initialized with {len(self.dataset_fields)} fields")
        logger.info(f"System timezone: {local_tz}, Current time: {get_local_timestamp()}")

    def _load_scalers(self):
        try:
            if os.path.exists(self.SCALER_FILE_PATH):
                logger.info(f"Loading scaler from {self.SCALER_FILE_PATH}")
                with open(self.SCALER_FILE_PATH, 'rb') as f:
                    scaler_data = pickle.load(f)
                self.feature_scaler = scaler_data['feature_scaler']
                self.target_scaler = scaler_data['target_scaler']
                self.feature_columns = scaler_data['feature_columns']
                self.input_dim = scaler_data['input_dim']
                logger.info(f"Scaler loaded successfully - {len(self.feature_columns)} features, dim={self.input_dim}")
            else:
                logger.warning(f"Scaler file not found: {self.SCALER_FILE_PATH}")
        except Exception as e:
            logger.error(f"Failed to load scaler: {e}")

    def load_data_from_csv(self):
        try:
            if not os.path.exists(self.CSV_FILE_PATH):
                logger.info(f"CSV file not found, will create new: {self.CSV_FILE_PATH}")
                return 0

            df = pd.read_csv(self.CSV_FILE_PATH)
            data_count = len(df)

            if data_count == 0:
                logger.warning("CSV file is empty")
                return 0

            logger.info(f"Loaded {data_count} records from CSV")
            latest_data = df.tail(self.BUFFER_SIZE)
            for _, row in latest_data.iterrows():
                try:
                    row_dict = row.to_dict()
                    if isinstance(row_dict.get('timestamp'), pd.Timestamp):
                        row_dict['timestamp'] = row_dict['timestamp'].isoformat()
                    data = SensorData(**row_dict)
                    self.sensor_data_buffer.append(data)
                except Exception as e:
                    logger.warning(f"Skipping invalid row: {e}")

            self.total_data_received = data_count
            logger.info(f"Buffer loaded with {len(self.sensor_data_buffer)} records")
            return data_count

        except Exception as e:
            logger.error(f"Failed to load CSV: {e}")
            return 0

    def save_data_to_csv(self, data: SensorData):
        try:
            data_dict = data.model_dump()
            
            timestamp_str = data_dict['timestamp']
            try:
                
                dt = pd.to_datetime(timestamp_str)
                data_dict['timestamp'] = dt.strftime('%Y-%m-%d %H:%M:%S')
            except Exception as e:
                
                logger.warning(f"Timestamp parsing failed: {timestamp_str}, {e}")

            df_new = pd.DataFrame([data_dict])
            if not os.path.exists(self.CSV_FILE_PATH):
                df_new.to_csv(self.CSV_FILE_PATH, index=False, mode='w')
            else:
                df_new.to_csv(self.CSV_FILE_PATH, index=False, mode='a', header=False)
            return True
        except Exception as e:
            logger.error(f"Failed to save CSV: {e}")
            return False

    def get_csv_data_count(self) -> int:
        try:
            if not os.path.exists(self.CSV_FILE_PATH):
                return 0
            df = pd.read_csv(self.CSV_FILE_PATH)
            return len(df)
        except Exception as e:
            logger.error(f"Failed to get CSV count: {e}")
            return 0

    def read_latest_csv_data(self, limit: int = None) -> pd.DataFrame:
        try:
            if not os.path.exists(self.CSV_FILE_PATH):
                return pd.DataFrame()
            df = pd.read_csv(self.CSV_FILE_PATH)
            if limit is None:
                limit = self.BUFFER_SIZE
            return df.tail(limit)
        except Exception as e:
            logger.error(f"Failed to read latest CSV data: {e}")
            return pd.DataFrame()

    def load_model(self, model_path: str = None):
        try:
            if model_path is None:
                model_path = self.MODEL_PATH

            if os.path.exists(model_path):
                logger.info(f"Loading model from {model_path}")
                checkpoint = torch.load(model_path, map_location='cpu', weights_only=False)
                config = Seq2SeqV2Config()
                input_dim = 51
                model = ImprovedSeq2SeqModel(config, input_dim)

                if isinstance(checkpoint, dict):
                    if 'model_state_dict' in checkpoint:
                        model.load_state_dict(checkpoint['model_state_dict'])
                        logger.info(f"Model loaded - Epoch: {checkpoint.get('epoch', 'N/A')}, Val Loss: {checkpoint.get('val_loss', 'N/A'):.6f}")
                    else:
                        model.load_state_dict(checkpoint)
                else:
                    model = checkpoint

                model.eval()
                self.model = model

                scaler_path = self.SCALER_FILE_PATH
                if os.path.exists(scaler_path):
                    with open(scaler_path, 'rb') as f:
                        scaler_data = pickle.load(f)
                    self.feature_scaler = scaler_data['feature_scaler']
                    self.target_scaler = scaler_data['target_scaler']
                    logger.info(f"Scaler loaded - dim: {scaler_data.get('input_dim', 'N/A')}")
                else:
                    logger.warning("Scaler file not found, predictions may be inaccurate")

                logger.info(f"Model loaded: {config.HIDDEN_DIM}D x {config.NUM_LAYERS}L, seq={config.SEQ_LEN}, pred={config.PRED_LEN}")
                return True
            else:
                logger.warning(f"Model file not found: {model_path}")
                return False
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False

    def add_sensor_data(self, data: SensorData):
        if not self.save_data_to_csv(data):
            logger.error("Failed to save data to CSV")
            return None

        self.sensor_data_buffer.append(data)
        self.total_data_received += 1

        if len(self.sensor_data_buffer) > self.BUFFER_SIZE:
            self.sensor_data_buffer.pop(0)

        csv_count = self.get_csv_data_count()
        logger.info(f"Data received - VOCs: {data.rto_out_conc:.2f}, CSV: {csv_count}, Buffer: {len(self.sensor_data_buffer)}/{self.BUFFER_SIZE}")

        if self._should_predict():
            return self._trigger_prediction()
        return None

    def _should_predict(self) -> bool:
        csv_count = self.get_csv_data_count()
        if csv_count >= self.MIN_DATA_FOR_PREDICTION:
            logger.info(f"Prediction triggered - {csv_count} records")
            return True
        return False

    def _trigger_prediction(self) -> Optional[PredictionResult]:
        try:
            csv_count = self.get_csv_data_count()
            if csv_count < self.MIN_DATA_FOR_PREDICTION:
                logger.warning(f"Insufficient data: {csv_count} < {self.MIN_DATA_FOR_PREDICTION}")
                return None

            latest_df = self.read_latest_csv_data(self.BUFFER_SIZE)
            available_data = len(latest_df)

            self.sensor_data_buffer.clear()
            for _, row in latest_df.iterrows():
                try:
                    data = SensorData(**row.to_dict())
                    self.sensor_data_buffer.append(data)
                except Exception as e:
                    logger.warning(f"Skipping invalid row: {e}")

            logger.info(f"Loaded {available_data} records for prediction")

            if csv_count < self.BUFFER_SIZE:
                return self._warmup_prediction(available_data)
            else:
                return self._ai_prediction()

        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return None

    def _warmup_prediction(self, available_data_size: int) -> Optional[PredictionResult]:
        try:
            recent_data = self.sensor_data_buffer[-available_data_size:]
            vocs_values = [d.rto_out_conc for d in recent_data]
            avg_value = sum(vocs_values) / len(vocs_values)

            if len(vocs_values) >= 5:
                trend = (vocs_values[-1] - vocs_values[-5]) / 5
            else:
                trend = 0

            predicted_values = []
            for i in range(self.PREDICTION_HORIZON):
                predicted_value = max(0, avg_value + trend * (i / 60))
                predicted_value = min(100, predicted_value)
                predicted_values.append(predicted_value)

            if available_data_size >= 36:
                confidence = 0.75
                pred_type = "Warmup (9h)"
            elif available_data_size >= 24:
                confidence = 0.70
                pred_type = "Warmup (6h)"
            elif available_data_size >= 12:
                confidence = 0.60
                pred_type = "Warmup (3h)"
            else:
                confidence = 0.50
                pred_type = "Warmup (<3h)"

            result = PredictionResult(
                timestamp=get_local_timestamp(),
                prediction_horizon=self.PREDICTION_HORIZON,
                predicted_values=predicted_values,
                confidence=confidence,
                alert_triggered=False,
                alert_message=f"Warmup prediction ({available_data_size}/{self.BUFFER_SIZE} points)",
                prediction_type=pred_type
            )

            self._check_alerts(result)
            self.latest_prediction = result
            self.predictions.append(result)
            self.total_predictions += 1

            logger.info(f"Warmup prediction - Timestamp: {result.timestamp}, Confidence: {confidence*100:.0f}%, Max: {max(predicted_values):.2f}")
            return result

        except Exception as e:
            logger.error(f"Warmup prediction failed: {e}")
            return None

    def _parse_timestamp(self, timestamp_str: str) -> pd.Timestamp:
        try:
            if 'T' in timestamp_str:
                return pd.to_datetime(timestamp_str)
            else:
                return pd.to_datetime(timestamp_str)
        except Exception as e:
            logger.warning(f"Timestamp parsing failed: {timestamp_str}, {e}")
            return pd.NaT

    def _extract_features(self) -> np.ndarray:
        try:
            data_list = []
            for data in self.sensor_data_buffer[-self.BUFFER_SIZE:]:
                data_dict = {
                    'timestamp': data.timestamp,
                    'ambient_temp': data.ambient_temp,
                    'ambient_humidity': data.ambient_humidity,
                    'ambient_pressure': data.ambient_pressure,
                    'coating_flow': data.coating_flow,
                    'coating_conc': data.coating_conc,
                    'coating_temp': data.coating_temp,
                    'coating_pressure': data.coating_pressure,
                    'rotor_speed': data.rotor_speed,
                    'adsorption_fan_power': data.adsorption_fan_power,
                    'desorption_fan_power': data.desorption_fan_power,
                    'rotor_inlet_temp': data.rotor_inlet_temp,
                    'rotor_inlet_humid': data.rotor_inlet_humid,
                    'desorption_temp': data.desorption_temp,
                    'concentrated_flow': data.concentrated_flow,
                    'concentrated_conc': data.concentrated_conc,
                    'concentrated_temp': data.concentrated_temp,
                    'concentrated_pressure': data.concentrated_pressure,
                    'rto_in_flow': data.rto_in_flow,
                    'rto_in_temp': data.rto_in_temp,
                    'rto_in_pressure': data.rto_in_pressure,
                    'burner_gas_flow': data.burner_gas_flow,
                    'combustion_temp': data.combustion_temp,
                    'rto_in_conc': data.rto_in_conc,
                    'rto_out_conc': data.rto_out_conc,
                    'rto_out_temp': data.rto_out_temp
                }
                data_list.append(data_dict)

            df = pd.DataFrame(data_list)
            logger.info(f"Feature extraction - Raw data: {df.shape}")

            df['timestamp'] = df['timestamp'].apply(self._parse_timestamp)
            df['hour_sin'] = np.sin(2 * np.pi * df['timestamp'].dt.hour / 24)
            df['hour_cos'] = np.cos(2 * np.pi * df['timestamp'].dt.hour / 24)
            df['weekday_sin'] = np.sin(2 * np.pi * df['timestamp'].dt.weekday / 7)
            df['weekday_cos'] = np.cos(2 * np.pi * df['timestamp'].dt.weekday / 7)
            df['month_sin'] = np.sin(2 * np.pi * df['timestamp'].dt.month / 12)
            df['month_cos'] = np.cos(2 * np.pi * df['timestamp'].dt.month / 12)

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

            exclude_cols = ['timestamp', 'rto_out_conc']
            feature_columns = [col for col in df.columns if col not in exclude_cols]
            X = df[feature_columns].values
            y = df['rto_out_conc'].values.reshape(-1, 1)

            if hasattr(self.feature_scaler, 'scale_'):
                X_scaled = self.feature_scaler.transform(X)
                y_scaled = self.target_scaler.transform(y)
            else:
                logger.warning("Fitting new scalers - predictions may be inconsistent")
                self.feature_scaler.fit(X)
                self.target_scaler.fit(y)
                X_scaled = self.feature_scaler.transform(X)
                y_scaled = self.target_scaler.transform(y)

            X_with_hist = np.concatenate([X_scaled, y_scaled], axis=1)
            features = X_with_hist.astype(np.float32)

            expected_shape = (96, 51)
            if features.shape != expected_shape:
                if features.shape[0] != 96:
                    logger.error(f"Invalid sequence length: {features.shape[0]}, expected 96")
                    return None
                if features.shape[1] != 51:
                    if features.shape[1] > 51:
                        features = features[:, :51]
                    else:
                        padding = np.zeros((96, 51 - features.shape[1]), dtype=np.float32)
                        features = np.concatenate([features, padding], axis=1)

            logger.info(f"Features extracted: {features.shape}")
            return features

        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            return None

    def _ai_prediction(self) -> Optional[PredictionResult]:
        try:
            if self.model is None:
                logger.warning("Model not loaded, using warmup prediction")
                return self._warmup_prediction(self.BUFFER_SIZE)

            features = self._extract_features()
            if features is None:
                logger.error("Feature extraction failed, falling back to warmup")
                return self._warmup_prediction(self.BUFFER_SIZE)

            features_tensor = torch.FloatTensor(features).unsqueeze(0)

            with torch.no_grad():
                predictions = self.model(features_tensor)

            if isinstance(predictions, torch.Tensor):
                predicted_values_normalized = predictions.squeeze().cpu().numpy()
                predicted_values = self.target_scaler.inverse_transform(
                    predicted_values_normalized.reshape(-1, 1)
                ).flatten()
            else:
                logger.warning("Invalid model output, using warmup")
                return self._warmup_prediction(self.BUFFER_SIZE)

            predicted_values = np.clip(predicted_values, 0, 500)

            result = PredictionResult(
                timestamp=get_local_timestamp(),
                prediction_horizon=self.PREDICTION_HORIZON,
                predicted_values=predicted_values.tolist(),
                confidence=0.85,
                alert_triggered=False,
                alert_message="AI model prediction",
                prediction_type=""
            )

            self._check_alerts(result)
            self.latest_prediction = result
            self.predictions.append(result)
            self.total_predictions += 1

            logger.info(f"AI prediction complete - Timestamp: {result.timestamp}, Max: {max(predicted_values):.2f}")
            return result

        except Exception as e:
            logger.error(f"AI prediction failed: {e}")
            return self._warmup_prediction(self.BUFFER_SIZE)

    def _check_alerts(self, prediction: PredictionResult):
        max_value = max(prediction.predicted_values)
        if max_value > self.ALERT_THRESHOLD:
            now_local = datetime.now().astimezone()
            alert = Alert(
                alert_id=f"ALT-{now_local.strftime('%Y%m%d%H%M%S')}",
                timestamp=get_local_timestamp(),
                level="critical" if max_value > 100 else "warning",
                message=f"VOCs threshold exceeded! Max: {max_value:.2f}, Threshold: {self.ALERT_THRESHOLD}",
                value=max_value,
                threshold=self.ALERT_THRESHOLD,
                acknowledged=False
            )
            self.alerts.insert(0, alert)
            self.total_alerts += 1
            if len(self.alerts) > 100:
                self.alerts.pop()
            prediction.alert_triggered = True
            prediction.alert_message = alert.message
            logger.warning(f"Alert triggered: {alert.message}")

    def get_latest_sensor_data(self) -> Optional[SensorData]:
        if self.sensor_data_buffer:
            return self.sensor_data_buffer[-1]
        return None

    def get_system_status(self) -> Dict:
        uptime = datetime.now() - self.system_start_time
        hours, remainder = divmod(uptime.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        csv_count = self.get_csv_data_count()

        return {
            "system_name": "VOCs Control System",
            "version": "2.2.0",
            "status": "running",
            "model_loaded": self.model is not None,
            "data_fields_count": len(self.dataset_fields),
            "data_categories": {
                "meteorological": 3,
                "equipment": 19,
                "gas_concentration": 3
            },
            "data_collection_interval_minutes": self.DATA_COLLECTION_INTERVAL,
            "prediction_interval_minutes": self.PREDICTION_INTERVAL,
            "prediction_horizon_minutes": self.PREDICTION_HORIZON,
            "alert_threshold_mg_m3": self.ALERT_THRESHOLD,
            "total_data_received": self.total_data_received,
            "total_predictions": self.total_predictions,
            "total_alerts": self.total_alerts,
            "csv_file_path": self.CSV_FILE_PATH,
            "csv_total_records": csv_count,
            "memory_buffer_size": len(self.sensor_data_buffer),
            "memory_buffer_status": f"{len(self.sensor_data_buffer)}/{self.BUFFER_SIZE}",
            "system_phase": self._get_system_phase(),
            "storage_type": "CSV",
            "model_architecture": "ImprovedSeq2Seq",
            "seq_len": 96,
            "pred_len": 24,
            "uptime": f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        }

    def _get_system_phase(self) -> str:
        csv_count = self.get_csv_data_count()
        if csv_count < self.MIN_DATA_FOR_PREDICTION:
            return f"Initializing ({csv_count} < {self.MIN_DATA_FOR_PREDICTION})"
        elif csv_count < self.BUFFER_SIZE:
            return f"Warmup ({csv_count}/{self.BUFFER_SIZE})"
        else:
            return f"Stable (AI active, {csv_count} records)"


system_manager = VOCsSystemManager()


class SSEManager:
    def __init__(self):
        self.clients = set()

    def add_client(self, client_queue):
        self.clients.add(client_queue)
        logger.info(f"SSE client connected - Total: {len(self.clients)}")

    def remove_client(self, client_queue):
        self.clients.discard(client_queue)
        logger.info(f"SSE client disconnected - Total: {len(self.clients)}")

    async def broadcast(self, message: dict):
        if not self.clients:
            return
        sse_message = f"data: {json.dumps(message, ensure_ascii=False)}\n\n"
        disconnected = set()
        for client_queue in self.clients:
            try:
                await client_queue.put(sse_message)
            except Exception as e:
                logger.error(f"SSE send failed: {e}")
                disconnected.add(client_queue)
        for client in disconnected:
            self.remove_client(client)


sse_manager = SSEManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("="*60)
    logger.info("VOCs Control System starting...")
    logger.info("="*60)

    model_loaded = system_manager.load_model()
    if model_loaded:
        logger.info("Model loaded successfully")
    else:
        logger.warning("Model not loaded, using warmup predictions")

    logger.info("Loading CSV data...")
    csv_data_count = system_manager.load_data_from_csv()

    if csv_data_count >= system_manager.MIN_DATA_FOR_PREDICTION:
        logger.info("Running initial prediction...")
        try:
            first_prediction = system_manager._trigger_prediction()
            if first_prediction:
                logger.info(f"Initial prediction - Type: {first_prediction.prediction_type}, Max: {max(first_prediction.predicted_values):.2f}")
            else:
                logger.warning("Initial prediction failed")
        except Exception as e:
            logger.error(f"Initial prediction error: {e}")
    else:
        logger.info(f"Insufficient data ({csv_data_count} < {system_manager.MIN_DATA_FOR_PREDICTION}), waiting for data")

    logger.info("="*60)
    logger.info(f"System ready - {len(system_manager.dataset_fields)} fields, {csv_data_count} records")


    yield

    logger.info("System shutting down...")


app = FastAPI(
    title="VOCs Control System",
    version="2.2.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "system": "VOCs Control System",
        "version": "2.2.0",
        "status": "running",
        "data_fields": 26,
        "data_categories": {
            "meteorological": 3,
            "equipment": 19,
            "gas_concentration": 3
        },
        "model_info": {
            "architecture": "ImprovedSeq2Seq",
            "seq_len": 96,
            "pred_len": 24,
            "hidden_dim": 256,
            "num_layers": 3
        },
        "endpoints": {
            "status": "/status",
            "receive_data": "/sensor-data",
            "predictions": "/predictions",
            "alerts": "/alerts",
            "events": "/events"
        }
    }


@app.get("/status")
async def get_status():
    return system_manager.get_system_status()


@app.post("/sensor-data")
async def receive_sensor_data(data: SensorData):
    prediction_result = system_manager.add_sensor_data(data)
    await sse_manager.broadcast({
        "type": "sensor_data",
        "timestamp": get_local_timestamp(),
        "data": data.model_dump()
    })
    if prediction_result:
        await sse_manager.broadcast({
            "type": "prediction",
            "timestamp": get_local_timestamp(),
            "data": prediction_result.model_dump()
        })
    return {
        "success": True,
        "message": "Data received",
        "data_received": {
            "timestamp": data.timestamp,
            "rto_out_conc": data.rto_out_conc
        },
        "prediction_triggered": prediction_result is not None,
        "system_phase": system_manager._get_system_phase(),
        "buffer_size": len(system_manager.sensor_data_buffer)
    }


@app.get("/predictions", response_model=List[PredictionResult])
async def get_predictions(limit: int = 10):
    return system_manager.predictions[-limit:]


@app.get("/predictions/latest", response_model=Optional[PredictionResult])
async def get_latest_prediction():
    return system_manager.latest_prediction


@app.get("/alerts", response_model=List[Alert])
async def get_alerts(limit: int = 50):
    return system_manager.alerts[:limit]


@app.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    for alert in system_manager.alerts:
        if alert.alert_id == alert_id:
            alert.acknowledged = True
            return {"success": True, "message": "Alert acknowledged"}
    raise HTTPException(status_code=404, detail="Alert not found")


@app.get("/sensor-data/latest")
async def get_latest_sensor_data():
    data = system_manager.get_latest_sensor_data()
    if data:
        return data.model_dump()
    return {"message": "No data"}


@app.get("/events")
async def sse_events():
    async def event_generator():
        client_queue = asyncio.Queue()
        sse_manager.add_client(client_queue)
        try:
            yield f"data: {json.dumps({'type': 'connected', 'message': 'SSE connected'}, ensure_ascii=False)}\n\n"
            while True:
                message = await client_queue.get()
                yield message
        except asyncio.CancelledError:
            logger.info("SSE connection cancelled")
        finally:
            sse_manager.remove_client(client_queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


def main():
    
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")


if __name__ == "__main__":
    main()
