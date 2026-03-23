import requests
import json
import time
from datetime import datetime
import random

BASE_URL = "http://127.0.0.1:8001"
API_BASE = f"{BASE_URL}/"


def generate_sensor_data(timestamp: str, vocs_conc: float = 23.0) -> dict:
    """Generate complete sensor data with 26 fields"""
    def add_noise(value, noise_level=0.1):
        return value + random.uniform(-noise_level * value, noise_level * value)
    
    return {
        "timestamp": timestamp,
        "ambient_temp": add_noise(21.5, 0.2),
        "ambient_humidity": add_noise(63.5, 0.3),
        "ambient_pressure": add_noise(101.3, 0.01),
        "coating_flow": add_noise(8500, 0.1),
        "coating_conc": add_noise(45, 0.2),
        "coating_temp": add_noise(26, 0.1),
        "coating_pressure": add_noise(101.2, 0.02),
        "rotor_speed": add_noise(4.7, 0.05),
        "adsorption_fan_power": add_noise(44, 0.1),
        "desorption_fan_power": add_noise(3.5, 0.1),
        "rotor_inlet_temp": add_noise(26, 0.1),
        "rotor_inlet_humid": add_noise(65, 0.1),
        "desorption_temp": add_noise(205, 0.05),
        "concentrated_flow": add_noise(850, 0.1),
        "concentrated_conc": 400.0,
        "concentrated_temp": add_noise(185, 0.1),
        "concentrated_pressure": add_noise(101.6, 0.02),
        "rto_in_flow": add_noise(1000, 0.02),
        "rto_in_temp": add_noise(185, 0.05),
        "rto_in_pressure": add_noise(101.5, 0.02),
        "burner_gas_flow": add_noise(11, 0.1),
        "combustion_temp": add_noise(757.8, 0.02),
        "rto_in_conc": add_noise(vocs_conc * 4, 0.15),
        "rto_out_conc": round(vocs_conc, 2),
        "rto_out_temp": add_noise(62, 0.15)
    }


def test_system_status():
    """Test: Get system status"""
    print("\n" + "="*60)
    print("Test 1: System Status")
    print("="*60)

    response = requests.get(f"{API_BASE}/status")
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print("Response:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(f"Failed: {response.text}")

    return response.status_code == 200


def test_send_sensor_data_single():
    """Test: Send single sensor data"""
    print("\n" + "="*60)
    print("Test 2: Send Sensor Data (26 fields)")
    print("="*60)

    timestamp = datetime.now().isoformat()
    sensor_data = generate_sensor_data(timestamp, vocs_conc=30.5)

    print(f"Sending data:")
    print(f"  Timestamp: {sensor_data['timestamp']}")
    print(f"  VOCs Outlet: {sensor_data['rto_out_conc']} mg/m³")
    print(f"  Ambient Temp: {sensor_data['ambient_temp']} °C")
    print(f"  RTO Inlet Temp: {sensor_data['rto_in_temp']} °C")

    response = requests.post(f"{API_BASE}/sensor-data", json=sensor_data)
    print(f"\nStatus Code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print("Success:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Failed: {response.text}")

    return response.status_code == 200


def test_send_data_simulation(duration_minutes: int = 20, interval_seconds: int = 60):
    """Test: Simulate continuous data collection and prediction"""
    print("\n" + "="*80)
    print(f"Test 3: Continuous Data Simulation ({duration_minutes} minutes)")
    print("="*80)
    print("Details:")
    print(f"  - Send sensor data every {interval_seconds} seconds")
    print("  - Trigger prediction when data is sufficient")
    print("  - VOCs concentration gradually increases to test alerts")
    print("="*80)

    base_vocs = 75.0

    for minute in range(1, duration_minutes + 1):
        vocs_conc = base_vocs + (minute * 0.8) + random.uniform(-1, 1)
        timestamp = datetime.now().isoformat()
        sensor_data = generate_sensor_data(timestamp, vocs_conc)

        print(f"\n[{minute:02d}/{duration_minutes}] Sending data | VOCs: {vocs_conc:.2f} mg/m³")

        response = requests.post(f"{API_BASE}/sensor-data", json=sensor_data)

        if response.status_code == 200:
            result = response.json()

            if result.get('prediction_triggered'):
                print(f"  Prediction triggered | Buffer: {result['buffer_size']}")

                pred_response = requests.get(f"{API_BASE}/predictions/latest")
                if pred_response.status_code == 200:
                    prediction = pred_response.json()
                    if prediction:
                        max_pred = max(prediction['predicted_values'])
                        print(f"  Type: {prediction.get('prediction_type', 'N/A')}")
                        print(f"  Max (6h): {max_pred:.2f} mg/m³")
                        print(f"  Confidence: {prediction['confidence'] * 100:.1f}%")

                        if prediction['alert_triggered']:
                            print(f"  ALERT: {prediction['alert_message']}")
        else:
            print(f"  Failed: {response.text}")

        if minute < duration_minutes:
            time.sleep(interval_seconds)

    print("\nSimulation complete!")


def test_get_predictions():
    """Test: Get prediction results"""
    print("\n" + "="*60)
    print("Test 4: Get Predictions")
    print("="*60)

    response = requests.get(f"{API_BASE}/predictions?limit=5")
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        predictions = response.json()
        print(f"Retrieved {len(predictions)} predictions")

        for i, pred in enumerate(predictions, 1):
            print(f"\nPrediction #{i}:")
            print(f"  Time: {pred['timestamp']}")
            print(f"  Type: {pred.get('prediction_type', 'N/A')}")
            print(f"  Horizon: {pred['prediction_horizon']} min")
            if pred['predicted_values']:
                max_val = max(pred['predicted_values'])
                print(f"  Max Value: {max_val:.2f} mg/m³")
            print(f"  Confidence: {pred['confidence'] * 100:.1f}%")
            print(f"  Alert: {'Yes' if pred['alert_triggered'] else 'No'}")
    else:
        print(f"Failed: {response.text}")


def test_get_alerts():
    """Test: Get alert list"""
    print("\n" + "="*60)
    print("Test 5: Get Alerts")
    print("="*60)

    response = requests.get(f"{API_BASE}/alerts?limit=10")
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        alerts = response.json()
        print(f"Retrieved {len(alerts)} alerts")

        if alerts:
            for i, alert in enumerate(alerts[:5], 1):
                print(f"\nAlert #{i}:")
                print(f"  ID: {alert['alert_id']}")
                print(f"  Level: {alert['level']}")
                print(f"  Message: {alert['message']}")
                print(f"  Value: {alert['value']:.2f} mg/m³")
                print(f"  Threshold: {alert['threshold']:.2f} mg/m³")
                print(f"  Acknowledged: {'Yes' if alert['acknowledged'] else 'No'}")
        else:
            print("  No alerts")
    else:
        print(f"Failed: {response.text}")


def test_acknowledge_alert(alert_id: str):
    """Test: Acknowledge an alert"""
    print("\n" + "="*60)
    print(f"Test: Acknowledge Alert - {alert_id}")
    print("="*60)

    response = requests.post(f"{API_BASE}/alerts/{alert_id}/acknowledge")
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print("Success:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Failed: {response.text}")


def test_get_latest_sensor_data():
    """Test: Get latest sensor data"""
    print("\n" + "="*60)
    print("Test: Get Latest Sensor Data")
    print("="*60)

    response = requests.get(f"{API_BASE}/sensor-data/latest")
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        if "message" not in data:
            print("Latest data received:")
            print(f"  Timestamp: {data.get('timestamp')}")
            print(f"  VOCs Outlet: {data.get('rto_out_conc')} mg/m³")
            print(f"  Ambient Temp: {data.get('ambient_temp')} °C")
            print(f"  RTO Inlet Temp: {data.get('rto_in_temp')} °C")
        else:
            print(data.get("message"))
    else:
        print(f"Failed: {response.text}")


def main():
    """Main test function"""
    print("\n" + "="*80)
    print("VOCs Control System - API Test Suite".center(80))
    print("="*80)

    try:
        test_system_status()
        test_send_sensor_data_single()
        test_get_predictions()
        test_get_alerts()
        test_get_latest_sensor_data()

        print("\n" + "="*80)
        print("Basic tests completed!")
        print("="*80)

    except requests.exceptions.ConnectionError:
        print("\nConnection failed! Ensure API server is running:")
        print("   python vocs_server.py")
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='VOCs System API Test Suite')
    parser.add_argument('--simulate', '-s', type=int, metavar='MINUTES',
                       help='Run continuous simulation (default: 20 minutes)')
    parser.add_argument('--interval', '-i', type=int, metavar='SECONDS', default=60,
                       help='Data sending interval in seconds (default: 60)')
    parser.add_argument('--alerts', '-a', action='store_true',
                       help='View alert list')
    parser.add_argument('--predictions', '-p', action='store_true',
                       help='View prediction results')
    parser.add_argument('--acknowledge', '-k', type=str, metavar='ALERT_ID',
                       help='Acknowledge specific alert')
    parser.add_argument('--latest', '-l', action='store_true',
                       help='View latest sensor data')

    args = parser.parse_args()

    if args.simulate:
        test_send_data_simulation(args.simulate, args.interval)
    elif args.alerts:
        test_get_alerts()
    elif args.predictions:
        test_get_predictions()
    elif args.acknowledge:
        test_acknowledge_alert(args.acknowledge)
    elif args.latest:
        test_get_latest_sensor_data()
    else:
        main()
