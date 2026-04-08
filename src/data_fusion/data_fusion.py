import pandas as pd
import numpy as np
import json
import os
import sqlite3
from typing import List, Dict, Union, Optional
import warnings
warnings.filterwarnings('ignore')

STANDARD_FIELDS = [
    'timestamp', 'ambient_temp', 'ambient_humidity', 'ambient_pressure',
    'coating_flow', 'coating_conc', 'coating_temp', 'coating_pressure',
    'rotor_speed', 'adsorption_fan_power', 'desorption_fan_power',
    'rotor_inlet_temp', 'rotor_inlet_humid', 'desorption_temp',
    'concentrated_flow', 'concentrated_conc', 'concentrated_temp', 'concentrated_pressure',
    'rto_in_flow', 'rto_in_conc', 'rto_in_temp', 'rto_in_pressure',
    'burner_gas_flow', 'combustion_temp',
    'rto_out_conc', 'rto_out_temp'
]

FIELD_DTYPES = {
    'timestamp': 'datetime64[ns]',
    'ambient_temp': float, 'ambient_humidity': float, 'ambient_pressure': float,
    'coating_flow': float, 'coating_conc': float, 'coating_temp': float, 'coating_pressure': float,
    'rotor_speed': float, 'adsorption_fan_power': float, 'desorption_fan_power': float,
    'rotor_inlet_temp': float, 'rotor_inlet_humid': float, 'desorption_temp': float,
    'concentrated_flow': float, 'concentrated_conc': float, 'concentrated_temp': float, 'concentrated_pressure': float,
    'rto_in_flow': float, 'rto_in_conc': float, 'rto_in_temp': float, 'rto_in_pressure': float,
    'burner_gas_flow': float, 'combustion_temp': float,
    'rto_out_conc': float, 'rto_out_temp': float
}

FIELD_RANGES = {
    'ambient_temp': (-10, 50),
    'ambient_humidity': (10, 100),
    'ambient_pressure': (90, 110),
    'coating_flow': (0, 20000),
    'coating_conc': (0, 200),
    'coating_temp': (15, 40),
    'coating_pressure': (90, 110),
    'rotor_speed': (0, 10),
    'adsorption_fan_power': (0, 100),
    'desorption_fan_power': (0, 10),
    'rotor_inlet_temp': (15, 40),
    'rotor_inlet_humid': (30, 80),
    'desorption_temp': (180, 250),
    'concentrated_flow': (0, 2000),
    'concentrated_conc': (200, 600),
    'concentrated_temp': (180, 200),
    'concentrated_pressure': (90, 110),
    'rto_in_flow': (0, 2000),
    'rto_in_conc': (200, 600),
    'rto_in_temp': (180, 200),
    'rto_in_pressure': (90, 110),
    'burner_gas_flow': (0, 100),
    'combustion_temp': (700, 900),
    'rto_out_conc': (0, 50),
    'rto_out_temp': (50, 100)
}

ALIGN_FREQUENCY = '1min'
FILL_STRATEGY = {
    'method': 'linear',
    'limit': 10
}


class VOCsMultiSourceFusion:
    def __init__(self, output_csv: str = 'output/fused_vocs_data.csv',
                 output_db: str = 'output/vocs_fusion.db',
                 db_table: str = 'vocs_unified_data'):
        self.output_csv = output_csv
        self.output_db = output_db
        self.db_table = db_table
        self.fused_data: Optional[pd.DataFrame] = None
        os.makedirs(os.path.dirname(output_csv), exist_ok=True)
        os.makedirs(os.path.dirname(output_db), exist_ok=True)

    def _parse_timestamp(self, ts: Union[str, int, float]) -> pd.Timestamp:
        try:
            if isinstance(ts, (int, float)) and ts > 1e12:
                return pd.to_datetime(ts, unit='ms')
            elif isinstance(ts, (int, float)) and ts > 1e9:
                return pd.to_datetime(ts, unit='s')
            else:
                return pd.to_datetime(ts, errors='coerce')
        except:
            return pd.NaT

    def _clean_single_source(self, df: pd.DataFrame, source_type: str) -> pd.DataFrame:
        print(f"\n清洗{source_type}数据源")

        df.columns = [col.lower().strip().replace(' ', '_') for col in df.columns]

        alias_mapping = {
            'env_temp': 'ambient_temp', 'env_hum': 'ambient_humidity',
            'atm_pressure': 'ambient_pressure', 'coating_vocs': 'coating_conc',
            'rto_comb_temp': 'combustion_temp', 'rto_out_vocs': 'rto_out_conc',
            'time': 'timestamp', 'datetime': 'timestamp', '采集时间': 'timestamp'
        }
        df = df.rename(columns=alias_mapping)

        if 'timestamp' not in df.columns:
            raise ValueError(f"{source_type}数据源缺少时间戳字段")
        df['timestamp'] = df['timestamp'].apply(self._parse_timestamp)
        df = df.dropna(subset=['timestamp'])

        df = df.reindex(columns=STANDARD_FIELDS, fill_value=np.nan)

        for field, dtype in FIELD_DTYPES.items():
            if field == 'timestamp':
                df[field] = df[field].astype(dtype)
            else:
                df[field] = pd.to_numeric(df[field], errors='coerce').astype(dtype, errors='ignore')

        for field, (min_val, max_val) in FIELD_RANGES.items():
            if field in df.columns:
                df[field] = np.clip(df[field], min_val, max_val)

        numeric_fields = [f for f in STANDARD_FIELDS if f != 'timestamp']
        df[numeric_fields] = df[numeric_fields].interpolate(
            method=FILL_STRATEGY['method'],
            limit=FILL_STRATEGY['limit'],
            limit_direction='both'
        )
        df[numeric_fields] = df[numeric_fields].fillna(df[numeric_fields].mean())

        df = df.drop_duplicates(subset=['timestamp'], keep='last')

        print(f"清洗完成：有效记录数={len(df)}, 字段数={len(df.columns)}")
        return df

    def load_csv(self, csv_paths: Union[str, List[str]]) -> pd.DataFrame:
        if isinstance(csv_paths, str):
            csv_paths = [csv_paths]

        csv_dfs = []
        for path in csv_paths:
            if not os.path.exists(path):
                print(f"警告：CSV文件不存在，跳过 -> {path}")
                continue
            df = pd.read_csv(path, encoding='utf-8-sig')
            csv_dfs.append(self._clean_single_source(df, 'CSV'))

        if not csv_dfs:
            raise ValueError("无有效CSV文件可加载")
        return pd.concat(csv_dfs, ignore_index=True)

    def load_excel(self, excel_paths: Union[str, List[str]], sheet_name: int = 0) -> pd.DataFrame:
        if isinstance(excel_paths, str):
            excel_paths = [excel_paths]

        excel_dfs = []
        for path in excel_paths:
            if not os.path.exists(path):
                print(f"警告：Excel文件不存在，跳过 -> {path}")
                continue
            df = pd.read_excel(path, sheet_name=sheet_name)
            excel_dfs.append(self._clean_single_source(df, 'Excel'))

        if not excel_dfs:
            raise ValueError("无有效Excel文件可加载")
        return pd.concat(excel_dfs, ignore_index=True)

    def load_json_stream(self, json_paths: Union[str, List[str]]) -> pd.DataFrame:
        if isinstance(json_paths, str):
            json_paths = [json_paths]

        json_records = []
        for path in json_paths:
            if not os.path.exists(path):
                print(f"警告：JSON文件不存在，跳过 -> {path}")
                continue
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        json_records.append(record)
                    except json.JSONDecodeError:
                        continue

        if not json_records:
            raise ValueError("无有效JSON实时流数据可加载")

        df = pd.DataFrame(json_records)
        return self._clean_single_source(df, 'JSON')

    def align_time_series(self, *data_frames: pd.DataFrame) -> pd.DataFrame:
        print("\n多源数据时序对齐")

        merged_df = pd.concat(data_frames, ignore_index=True)
        merged_df = merged_df.sort_values('timestamp')

        merged_df = merged_df.set_index('timestamp')
        resampled_df = merged_df.resample(ALIGN_FREQUENCY).agg({
            field: 'mean' for field in STANDARD_FIELDS if field != 'timestamp'
        })

        resampled_df = resampled_df.interpolate(
            method=FILL_STRATEGY['method'],
            limit=FILL_STRATEGY['limit'],
            limit_direction='both'
        )
        resampled_df = resampled_df.fillna(resampled_df.mean())

        resampled_df = resampled_df.reset_index()
        resampled_df['timestamp'] = resampled_df['timestamp'].dt.floor(ALIGN_FREQUENCY)

        resampled_df = resampled_df[STANDARD_FIELDS]
        for field, dtype in FIELD_DTYPES.items():
            if field != 'timestamp':
                resampled_df[field] = resampled_df[field].astype(dtype)

        print(f"时序对齐完成：")
        print(f"  - 时间范围：{resampled_df['timestamp'].min()} ~ {resampled_df['timestamp'].max()}")
        print(f"  - 对齐后记录数：{len(resampled_df)}")
        print(f"  - 统一粒度：{ALIGN_FREQUENCY}")

        self.fused_data = resampled_df
        return resampled_df

    def save_structured_data(self):
        if self.fused_data is None:
            raise ValueError("未完成时序对齐，无法存储数据")

        print("\n结构化存储融合数据")

        output_df = self.fused_data.copy()
        output_df['timestamp'] = output_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        for field in output_df.columns:
            if field != 'timestamp':
                output_df[field] = output_df[field].round(10)

        output_df.to_csv(self.output_csv, index=False, encoding='utf-8-sig')
        print(f"  - CSV文件已保存：{self.output_csv}")

        conn = sqlite3.connect(self.output_db)
        self.fused_data['timestamp'] = pd.to_datetime(self.fused_data['timestamp'])
        self.fused_data.to_sql(
            name=self.db_table,
            con=conn,
            if_exists='replace',
            index=False
        )
        conn.close()
        print(f"  - SQLite数据库已保存：{self.output_db}（表名：{self.db_table}）")

        print("\n融合数据概览")
        print(f"  - 总记录数：{len(self.fused_data)}")
        print(f"  - 字段数：{len(self.fused_data.columns)}")

    def run_fusion(self, csv_paths: Optional[Union[str, List[str]]] = None,
                   excel_paths: Optional[Union[str, List[str]]] = None,
                   json_paths: Optional[Union[str, List[str]]] = None):
        print("="*80)
        print("VOCs多源数据融合流程启动")
        print("="*80)

        data_sources = []
        if csv_paths:
            csv_data = self.load_csv(csv_paths)
            data_sources.append(csv_data)
        if excel_paths:
            excel_data = self.load_excel(excel_paths)
            data_sources.append(excel_data)
        if json_paths:
            json_data = self.load_json_stream(json_paths)
            data_sources.append(json_data)

        if not data_sources:
            raise ValueError("未指定任何数据源（CSV/Excel/JSON）")

        self.align_time_series(*data_sources)
        self.save_structured_data()

        print("\n多源数据融合流程完成")
        return self.fused_data


if __name__ == "__main__":
    fusion = VOCsMultiSourceFusion(
        output_csv='src/data_fusion/output/fused_vocs_data.csv',
        output_db='src/data_fusion/output/vocs_fusion.db'
    )

    fusion.run_fusion(
        csv_paths='src/data_fusion/sample_data/vocs_history.csv',
        excel_paths='src/data_fusion/sample_data/vocs_meteorology.xlsx',
        json_paths='src/data_fusion/sample_data/vocs_realtime.json'
    )
