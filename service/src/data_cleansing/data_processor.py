import asyncio
import json
import io
import pandas as pd
import logging
from pathlib import Path
from typing import List, Dict, Union, Optional
from ..config import FRAME_SIZE  # Number of rows per frame

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self, queue: asyncio.Queue, frame_size: int = FRAME_SIZE, raw_csv_path: Optional[str] = None):
        self.queue = queue
        self.buffer: List[Dict] = []
        self.frame_size = frame_size
        
        # Initialize raw CSV file for streaming payloads
        self.raw_csv_path = None
        if raw_csv_path:
            self.raw_csv_path = Path(raw_csv_path)
            self.raw_csv_path.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"Raw CSV stream initialized: {self.raw_csv_path}")

    def process_data(self, data: Union[str, dict]):
        """
        Accept either a dict (parsed JSON) or a newline-delimited JSON/CSV string.
        Normalize column names (ir → photodiode_value) for feature extraction compatibility.
        Write raw payload to CSV file. Build small DataFrame chunks and append rows 
        to internal buffer. When buffer >= frame_size, queue a DataFrame frame.
        """
        # Accept pre-parsed JSON dict
        if isinstance(data, dict):
            df_chunk = pd.DataFrame([data])
            # Normalize column names: ir → photodiode_value
            if 'ir' in df_chunk.columns and 'photodiode_value' not in df_chunk.columns:
                df_chunk.rename(columns={'ir': 'photodiode_value'}, inplace=True)
            
            # Write raw dict to CSV
            if self.raw_csv_path:
                try:
                    df_chunk.to_csv(self.raw_csv_path, mode='a', header=not self.raw_csv_path.exists(), index=False)
                except Exception as e:
                    logger.warning(f"Failed to write raw CSV: {e}")
        else:
            # try JSON string first, then CSV fallback
            try:
                obj = json.loads(data)
                df_chunk = pd.DataFrame([obj]) if isinstance(obj, dict) else pd.DataFrame(obj)
                # Normalize column names
                if 'ir' in df_chunk.columns and 'photodiode_value' not in df_chunk.columns:
                    df_chunk.rename(columns={'ir': 'photodiode_value'}, inplace=True)
                
                # Write parsed JSON to CSV
                if self.raw_csv_path:
                    try:
                        df_chunk.to_csv(self.raw_csv_path, mode='a', header=not self.raw_csv_path.exists(), index=False)
                    except Exception as e:
                        logger.warning(f"Failed to write raw CSV: {e}")
            except (json.JSONDecodeError, TypeError):
                df_chunk = pd.read_csv(io.StringIO(data), header=None)

        # append rows to internal buffer
        for _, row in df_chunk.iterrows():
            self.buffer.append(row.to_dict())

        # when we have enough rows, create and enqueue a frame
        while len(self.buffer) >= self.frame_size:
            frame_df = pd.DataFrame(self.buffer[:self.frame_size])
            self.buffer = self.buffer[self.frame_size:]
            asyncio.create_task(self._queue_frame(frame_df))

    async def _queue_frame(self, frame_df: pd.DataFrame):
        await self.queue.put(frame_df)
