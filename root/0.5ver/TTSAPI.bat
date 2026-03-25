@echo off
@chcp 65001 >nul
cd C:\Users\Administrator\Downloads\GPT-SoVITS-v2pro-20250604
.\runtime\python api.py -a 0.0.0.0 -d cuda -p 3712 -s "SoVITS_weights_v2Pro/EVE-AIC-2_e10_s590.pth" -g "GPT_weights_v2Pro/EVE-AIC-2-e14.ckpt" -dr "第一次，我没有抗拒你们救走清扫者文明，你们不留下一点东西都别想离开.wav" -dt "第一次，我没有抗拒你们救走清扫者文明，你们不留下一点东西都别想离开" -dl zh
pause
