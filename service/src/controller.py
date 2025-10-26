import asyncio
import time
import logging
from pathlib import Path
import random 
from .data_cleansing.data_processor import DataProcessor 
from .bluetooth.ble_handler import BLEHandler 
from .feature_extraction.feature_vector import FeatureExtractor 
from .algorithm.baseline import load_baseline
from .algorithm.ml_models import load_models, predict_state
from .config import SAMPLE_RATE, BLINK_THRESHOLD, NOD_THRESHOLD
from .network.ws_server import WebSocketServer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RAW_DIR = Path("./data/raw")
PREPROCESSED_DIR = Path("./data/preprocessed")
RAW_DIR.mkdir(parents=True, exist_ok=True)
PREPROCESSED_DIR.mkdir(parents=True, exist_ok=True)

async def main():
    queue = asyncio.Queue()
    
    raw_csv_file = RAW_DIR / "live_payloads.csv"
    processor = DataProcessor(queue, raw_csv_path=str(raw_csv_file))
    handler = BLEHandler(data_callback=processor.process_data)
    extractor = FeatureExtractor(sample_rate=SAMPLE_RATE, blink_threshold=BLINK_THRESHOLD, nod_threshold=NOD_THRESHOLD)

    baseline = load_baseline()
    if baseline is None:
        raise RuntimeError("Baseline not found. Please create it before starting.")
    alert_model, drowsy_model = load_models()

    start_time = time.time()
    session_id = f"IRIS{random.randint(1000, 9999)}"
    
    state = {
        "connected": False,
        "duration": 0.0,
        "status": "Awaiting Hardware",
        "session_id": session_id,
        "metrics": {"avg_accel": 0.0, "blink_duration": 0.0, "nod_freq": 0.0}
    }

    bluetooth_task = asyncio.create_task(handler.connect_and_subscribe())

    ws_server = WebSocketServer(host="0.0.0.0") 
    ws_task = asyncio.create_task(ws_server.start())

    async def broadcast_state():
        while True:
            try:
                await ws_server.broadcast(state)
            except Exception as e:
                logger.debug(f"Broadcast error: {e}")
            await asyncio.sleep(1)
    
    broadcast_task = asyncio.create_task(broadcast_state())
    
    try:
        while True:
            try:
                frame = await asyncio.wait_for(queue.get(), timeout=1.0) 
            except asyncio.TimeoutError:
                # Keep broadcasting the last known state, don't change it
                continue 

            avg_accel = extractor.getAvgAccelScalar(frame)
            blink_duration = extractor.getBlinkScalar(frame)
            nod_freq = extractor.getNodFreqScalar(frame)

            avg_accel_py = float(avg_accel) 
            blink_duration_py = float(blink_duration)
            nod_freq_py = float(nod_freq)

            state_prediction = predict_state([blink_duration, nod_freq, avg_accel], alert_model, drowsy_model)

            if state_prediction == "Drowsy":
                driver_status = "Danger"
            elif blink_duration_py < 300 or avg_accel_py > 0.3:
                driver_status = "Be careful"
            else:
                driver_status = "Looking good"

            state.update({
                "connected": (
                    handler.client.is_connected if handler.client else False
                ),
                "duration": round(time.time() - start_time, 1),
                "status": driver_status,
                "session_id": session_id,
                "metrics": {
                    "avg_accel": avg_accel_py,
                    "blink_duration": blink_duration_py,
                    "nod_freq": nod_freq_py
                }
            })

            logger.info(f"State: {state}")
            queue.task_done()

    except asyncio.CancelledError:
        logger.info("Controller cancelled.")
    finally:
        await handler.stop()
        broadcast_task.cancel()
        ws_task.cancel()
        bluetooth_task.cancel()
        
        try:
            await broadcast_task
        except asyncio.CancelledError:
            pass
        try:
            await ws_task
        except asyncio.CancelledError:
            pass
        try:
            await bluetooth_task
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    asyncio.run(main())