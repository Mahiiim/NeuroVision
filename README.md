# NeuroDrishti

**NeuroDrishti** is an innovative Eye-Controlled Speech System designed to assist individuals with speech or motor impairments. By leveraging computer vision and facial landmarks, this application allows users to control their mouse cursor with head movements and trigger clicks by blinking or winking, enabling them to communicate through a virtual keyboard and quick phrases.

## Features
- **Head Movement Tracking:** Move your head to control the mouse cursor seamlessly on the screen.
- **Blink/Wink to Click:** Perform a blink or wink to trigger a mouse click.
- **Quick Phrases:** A dedicated control panel with pre-defined quick phrases (e.g., "I need help", "Yes", "No", "Water please") for fast communication.
- **Virtual Typing Station:** A full on-screen keyboard to type custom messages.
- **Text-to-Speech (TTS):** Integrated TTS engine to speak out the typed text or selected quick phrases.
- **Automatic Model Download:** Automatically fetches the required MediaPipe Face Landmarker model on the first run.

## Tech Stack
- Python
- OpenCV (`cv2`) for video capture and rendering
- MediaPipe for robust facial landmark detection
- PyAutoGUI for mouse control
- PyTTSx3 for Text-to-Speech
- Tkinter for the dashboard GUI

## Requirements
To run this project locally, make sure you have Python installed. Then, install the necessary dependencies:

```bash
pip install -r requirements.txt
```

## How to Use
1. Run the `main.py` script:
   ```bash
   python main.py
   ```
2. The **NeuroDrishti Dashboard** will appear. Click **START SYSTEM** to launch the tracking and communication panels.
3. Use your head to move the on-screen cursor.
4. Blink or wink to click on the quick phrases or type on the virtual keyboard.

## Notes
- To exit the application, you can press `ESC` or use the "EXIT APPLICATION" button on the screen.
- Make sure you are in a well-lit environment for optimal face tracking.
