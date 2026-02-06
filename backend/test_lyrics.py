import sys
import os

# Add the current directory to path so we can import process_song
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from process_song import clean_lyrics_with_paragraphs, generate_lyrics
from dotenv import load_dotenv

# Load .env for real API testing
load_dotenv()

def test_cleaning_logic():
    print("=== Testing clean_lyrics_with_paragraphs ===")
    
    test_cases = [
        {
            "name": "Mixed Case and Brackets",
            "input": "[Verse 1]\nHello world, how are you\n(chorus)\nTra la la, so ja baby\nVERSE 2: Papa is home",
            "expected_markers": 3
        },
        {
            "name": "Comma Splitting",
            "input": "Verse 1\nOne line, two line, three line",
            "expected_lines": 4 # Marker + 3 parts
        },
        {
            "name": "Existing Paragraphs",
            "input": "Verse 1\nLine A\n\nChorus\nLine B",
            "expected_markers": 2
        }
    ]

    for tc in test_cases:
        print(f"\nRunning test: {tc['name']}")
        output = clean_lyrics_with_paragraphs(tc['input'])
        print(f"Output:\n{output}\n")
        
        # Verify paragraph breaks (\n\n)
        paras = output.split('\n\n')
        print(f"Detected {len(paras)} paragraphs.")

def run_real_test():
    """Run this only if you want to use Gemini API credits"""
    print("\n=== Testing REAL generate_lyrics (Gemini Call) ===")
    try:
        result = generate_lyrics(
            baby_name="Liv Kaur",
            language="Hindi",
            characters=["Mummy", "Papa", "Dadu", "Dadi"],
            occasion="Lori"
        )
        print("\n--- GENERATED LYRICS ---")
        print(result.get('lyrics', 'No lyrics found'))
        print("\n--- IMAGE PROMPT ---")
        print(result.get('imagePrompt', 'No prompt found'))
    except Exception as e:
        print(f"Error calling Gemini: {e}")

if __name__ == "__main__":
    # test_cleaning_logic()
    
    # Run actual Gemini integration
    run_real_test()
