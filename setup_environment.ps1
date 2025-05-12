Write-Host "Activating virtual environment..."
.\gptenv\Scripts\Activate.ps1
Write-Host "Installing dependencies..."
pip install torch==2.1.0+cpu torchvision==0.16.0+cpu torchaudio==2.1.0+cpu -f https://download.pytorch.org/whl/cpu/torch_stable.html
pip install transformers