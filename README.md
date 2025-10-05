# STL_AI

STL 3D Model Recognition System - A complete machine learning pipeline for converting STL files to multi-angle images and performing FAISS-based object recognition.

## Features

- 🎯 STL to 360° multi-angle image generation
- 🤖 FAISS-based feature indexing with ResNet50
- 🌐 Web interface for training and prediction
- 🐳 Docker deployment support
- 📊 18 STL models with comprehensive training datasets

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Generate dataset from STL files
python generate_images_color.py

# Start web interface
./start_web.sh
# Access at http://localhost:5000
```

## Documentation

See [CLAUDE.md](CLAUDE.md) for complete documentation.

## Tech Stack

- PyVista, Trimesh - 3D rendering
- TensorFlow, ResNet50 - Deep learning
- FAISS - Feature search
- Flask - Web framework
- Docker - Deployment

## License

MIT
# STL_AI
