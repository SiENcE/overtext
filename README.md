# OverText

A real-time screen translation overlay tool that captures text from your screen, translates it, and displays the translation directly over the original content.

## Features

- **Real-time Translation Overlay**: Translates text on your screen and displays it in the same position as the original
- **Multiple Translation Services**: Supports Google Translate, DeepL, and Baidu Translation
- **Customizable Appearance**: Adjust text color, font, size, and window transparency
- **Smart Text Detection**: Uses EasyOCR to accurately detect text in various languages
- **Auto-Update Mode**: Continuously monitors screen content and updates translations when changes are detected
- **Dual-View Option**: View original OCR text alongside translations in a separate tabbed window

## Use Cases

- Translate foreign language games in real-time while playing
- Read international websites in your preferred language
- Translate software interfaces and documentation
- Follow video content in foreign languages
- Assist with language learning by showing side-by-side translations

## Installation

### Prerequisites

- Python 3.12 or higher
- Pip package manager

### Dependencies

OverText requires the following Python libraries:
- tkinter
- Pillow
- scikit-image
- deep-translator
- easyocr
- numpy

### Setup

1. Clone the repository:
```bash
git clone https://github.com/SiENcE/overtext.git
cd overtext
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

Note: Some systems may need to install tkinter separately:
- On Ubuntu/Debian: `sudo apt-get install python3-tk`
- On Fedora: `sudo dnf install python3-tkinter`
- On macOS with Homebrew: `brew install python-tk`
- On Windows: Tkinter is included with the standard Python installation

4. Start OverText:
```bash
python OverText.py
```

## Usage

### Basic Operation

1. Launch OverText
2. Position the transparent overlay window over the text you want to translate
3. Adjust the window size using the control panel or by dragging the edges
4. Set your source and target languages in the Translation tab
5. Click "Capture & Translate" to perform a one-time translation
6. For continuous translation, check "Auto Update" in the Capture tab

### Controls and Settings

#### Window Tab
- Adjust the width and height of the overlay
- Set the window transparency level
- Toggle the window frame on/off
- Show/hide the tabs window for viewing original OCR text

#### Appearance Tab
- Choose text color
- Select font family and size
- Toggle bold text formatting
- Set fixed font size or use auto-detected size based on original text

#### Translation Tab
- Set source language (use "auto" for automatic detection)
- Select target language
- Choose translation service (Google, DeepL, or Baidu)
- Enter API keys for premium services

#### Capture Tab
- Enable/disable auto-update mode
- Adjust update interval (how often the screen is checked for changes)
- Set change threshold (how much the screen must change to trigger a new translation)
- Choose comparison method for detecting changes

### Keyboard Shortcuts

- **Escape**: Quit application
- **Ctrl+T**: Capture and translate
- **Ctrl+C**: Clear translations
- **Ctrl+Tab**: Toggle tabs window

## Language Support

OverText supports a wide range of languages through the integrated OCR and translation services:

- For OCR: All languages supported by EasyOCR including English, Chinese, Japanese, Korean, Russian, and many European languages
- For translation: All languages supported by the selected translation service

Use standard language codes like:
- English: "en"
- German: "de"
- French: "fr"
- Spanish: "es"
- Japanese: "ja"
- Chinese: "zh"

## API Keys

For some translation services, you'll need to provide API keys:
- **DeepL**: Required for premium service with higher quota
- **Baidu**: Requires both App ID and API Key

## Known Limitations

- OCR accuracy may vary depending on text font, color, and background
- Some specialized terminology may not translate accurately
- Performance may be affected when translating large amounts of text
- Anti-aliased text on high-DPI screens may require additional tuning for best results

## Troubleshooting

**Text detection not working properly:**
- Try adjusting the window transparency for better OCR results
- Ensure high contrast between text and background
- Check that the correct source language is selected

**Slow performance:**
- Reduce the overlay window size to capture less area
- Increase the update interval in auto-update mode
- Use a smaller font size

**Translation errors:**
- Verify API keys are entered correctly
- Check internet connection
- Ensure language codes are valid

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License - see the [LICENSE](LICENSE) file for details.

This means:
- You are free to share (copy and redistribute) and adapt (remix, transform, and build upon) this material
- You must give appropriate credit and indicate if changes were made
- You may not use the material for commercial purposes
- No additional restrictions — you may not apply legal terms or technological measures that legally restrict others from doing anything the license permits

## Acknowledgments

- [EasyOCR](https://github.com/JaidedAI/EasyOCR) for text recognition
- [deep-translator](https://github.com/nidhaloff/deep-translator) for translation services
- [Pillow](https://python-pillow.org/) for image processing
- [scikit-image](https://scikit-image.org/) for image comparison
