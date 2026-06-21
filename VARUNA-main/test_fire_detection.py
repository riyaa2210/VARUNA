"""
Fire Detection Model Inference & Testing Script

Test your trained fire detection model on:
- Images
- Videos
- Real-time camera feed
"""

import os
import sys
from pathlib import Path
import argparse
import cv2

try:
    from ultralytics import YOLO
except ImportError:
    print("[ERROR] ultralytics not found. Installing...")
    os.system("pip install ultralytics")
    from ultralytics import YOLO

def detect_fires_image(model, image_path, conf=0.25, save=True):
    """Detect fires in a single image"""
    print(f"\n[INFERENCE] Processing image: {image_path}")
    
    results = model.predict(
        source=image_path,
        conf=conf,
        save=save,
        verbose=False,
        device=0
    )
    
    # Print results
    for result in results:
        n_fires = len(result.boxes)
        print(f"[RESULT] Detected {n_fires} fire(s)")
        
        for box in result.boxes:
            conf_score = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            print(f"  └─ Fire detected at ({x1}, {y1}) - ({x2}, {y2}) | Confidence: {conf_score:.2%}")
    
    if save:
        print(f"[OK] Result saved to: runs/detect/predict/")
    
    return results

def detect_fires_video(model, video_path, conf=0.25, output_path=None, max_frames=None):
    """Detect fires in a video"""
    print(f"\n[INFERENCE] Processing video: {video_path}")
    
    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open video: {video_path}")
        return
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"[INFO] Video: {width}x{height} @ {fps} FPS | Total frames: {total_frames}")
    
    # Setup output video
    if output_path:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    else:
        out = None
    
    frame_count = 0
    fire_frames = 0
    
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Limit frames if specified
            if max_frames and frame_count > max_frames:
                break
            
            # Run inference
            results = model(frame, conf=conf, verbose=False, device=0)
            
            # Draw results
            annotated_frame = results[0].plot()
            
            # Count fires
            n_fires = len(results[0].boxes)
            if n_fires > 0:
                fire_frames += 1
                cv2.putText(annotated_frame, f'🔥 FIRE DETECTED ({n_fires})', (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            # Add frame counter
            cv2.putText(annotated_frame, f'Frame: {frame_count}/{total_frames}', (10, height-20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
            
            # Save frame if output specified
            if out:
                out.write(annotated_frame)
            
            # Display progress
            if frame_count % int(fps) == 0:  # Every second
                print(f"  Processing: {frame_count}/{total_frames} frames | Fires detected: {fire_frames}")
    
    finally:
        cap.release()
        if out:
            out.release()
        
        print(f"\n[RESULT] Video Analysis Complete")
        print(f"  Total frames: {frame_count}")
        print(f"  Frames with fire: {fire_frames}")
        print(f"  Fire detection rate: {fire_frames/frame_count*100:.1f}%")
        
        if output_path:
            print(f"  Output saved to: {output_path}")

def detect_fires_realtime(model, camera_index=0, conf=0.25, duration=30):
    """Detect fires real-time from camera"""
    print(f"\n[INFERENCE] Starting real-time fire detection from camera {camera_index}")
    print(f"Duration: {duration} seconds | Confidence threshold: {conf}")
    
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open camera {camera_index}")
        return
    
    frame_count = 0
    fire_detections = 0
    
    print("[INFO] Press 'q' to quit")
    
    import time
    start_time = time.time()
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        # Resize for faster inference
        frame_small = cv2.resize(frame, (640, 480))
        
        # Run inference
        results = model(frame_small, conf=conf, verbose=False, device=0)
        annotated_frame = results[0].plot()
        
        # Count fires
        n_fires = len(results[0].boxes)
        if n_fires > 0:
            fire_detections += 1
            cv2.putText(annotated_frame, f'🔥 FIRE ALERT ({n_fires})', (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
        
        # Display FPS
        fps = frame_count / (time.time() - start_time)
        cv2.putText(annotated_frame, f'FPS: {fps:.1f} | Fires: {fire_detections}', (10, frame_small.shape[0]-20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 1)
        
        # Show frame
        cv2.imshow('Fire Detection (Press Q to quit)', annotated_frame)
        
        # Check timeout
        if time.time() - start_time > duration:
            print(f"\n[INFO] Duration limit ({duration}s) reached. Stopping...")
            break
        
        # Check for quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("[INFO] User quit")
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    print(f"\n[RESULT] Real-time Analysis Complete")
    print(f"  Total frames: {frame_count}")
    print(f"  Fire detections: {fire_detections}")
    print(f"  Average FPS: {frame_count / (time.time() - start_time):.1f}")

def main():
    parser = argparse.ArgumentParser(description='Test fire detection model')
    parser.add_argument('--model', type=str, default='backend/models/fire_detection.pt',
                       help='Path to trained model')
    parser.add_argument('--source', type=str, help='Image, video, or camera (0, 1, etc.)')
    parser.add_argument('--conf', type=float, default=0.25, help='Confidence threshold')
    parser.add_argument('--output', type=str, help='Output video path')
    parser.add_argument('--camera', action='store_true', help='Use camera instead of file')
    parser.add_argument('--camera-id', type=int, default=0, help='Camera index')
    parser.add_argument('--duration', type=int, default=30, help='Duration for camera mode (seconds)')
    parser.add_argument('--max-frames', type=int, help='Maximum frames to process')
    
    args = parser.parse_args()
    
    # Load model
    print("=" * 60)
    print("  🔥 FIRE DETECTION INFERENCE 🔥")
    print("=" * 60)
    
    if not Path(args.model).exists():
        print(f"[ERROR] Model not found: {args.model}")
        print("\nTrain a model first:")
        print("  python train_fire_detection.py")
        return
    
    print(f"\n[LOADING] Loading model: {args.model}")
    model = YOLO(args.model)
    print("[OK] Model loaded successfully")
    
    # Process source
    if args.camera or (args.source and args.source.isdigit()):
        # Real-time camera
        detect_fires_realtime(model, args.camera_id, args.conf, args.duration)
    
    elif args.source:
        # Image or video file
        source_path = Path(args.source)
        
        if not source_path.exists():
            print(f"[ERROR] File not found: {args.source}")
            return
        
        # Check if image or video
        image_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}
        video_exts = {'.mp4', '.avi', '.mov', '.mkv', '.wmv'}
        
        if source_path.suffix.lower() in image_exts:
            detect_fires_image(model, str(source_path), args.conf, save=True)
        
        elif source_path.suffix.lower() in video_exts:
            detect_fires_video(model, str(source_path), args.conf, args.output, args.max_frames)
        
        else:
            print(f"[ERROR] Unsupported file format: {source_path.suffix}")
    
    else:
        # Show usage
        print("\n[INFO] No source specified. Usage:")
        print("\nTest on image:")
        print("  python test_fire_detection.py --source test_image.jpg")
        print("\nTest on video:")
        print("  python test_fire_detection.py --source test_video.mp4 --output result.mp4")
        print("\nReal-time camera:")
        print("  python test_fire_detection.py --camera")
        print("\nWith custom model and confidence:")
        print("  python test_fire_detection.py --model backend/models/fire_detection.pt --source video.mp4 --conf 0.3")

if __name__ == '__main__':
    main()
