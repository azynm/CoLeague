import os
import sys

# Add parent directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from commentator.commentator import generate_commentary_audio
from commentator.mock_data import MOCK_EVENTS_SCENARIO_1

def test_styles():
    print("=== Testing Commentary Styles ===")
    
    styles_to_test = ["martin_tyler", "peter_drury"]
    
    for style in styles_to_test:
        print(f"\n--- Running Style: {style} ---")
        try:
            audio_data = generate_commentary_audio(MOCK_EVENTS_SCENARIO_1, style=style)
            
            if audio_data:
                output_dir = "outputs"
                os.makedirs(output_dir, exist_ok=True)
                filepath = os.path.join(output_dir, f"test_{style}.mp3")
                with open(filepath, "wb") as f:
                    f.write(audio_data)
                print(f"Success! Saved output to {filepath}\n")
            else:
                print(f"Failed to generate audio for {style}.\n")
        except Exception as e:
            print(f"Error testing {style}: {e}")

if __name__ == "__main__":
    test_styles()
