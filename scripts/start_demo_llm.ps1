$ErrorActionPreference = "Stop"

$LlamaServer = if ($env:LLAMA_SERVER_BIN) { $env:LLAMA_SERVER_BIN } else { "llama-server" }
$Model = if ($env:LLM_MODEL) { $env:LLM_MODEL } else { "Qwen/Qwen3-8B-GGUF:Q4_K_M" }
$Port = if ($env:LLM_PORT) { $env:LLM_PORT } else { "8080" }
$Context = if ($env:LLM_CONTEXT_SIZE) { $env:LLM_CONTEXT_SIZE } else { "16384" }
$GpuLayers = if ($env:LLM_GPU_LAYERS) { $env:LLM_GPU_LAYERS } else { "99" }

if (-not (Get-Command $LlamaServer -ErrorAction SilentlyContinue)) {
    throw "llama-server was not found. Install llama.cpp with: winget install llama.cpp"
}

& $LlamaServer `
    -hf $Model `
    --host 0.0.0.0 `
    --port $Port `
    --ctx-size $Context `
    --n-gpu-layers $GpuLayers `
    --jinja
