# Image Resolution Using Agentic Workflow

This project helps you upscale, resize, evaluate, and publish image-processing outputs using a central configuration and guided agent workflows.

The goal is simple: one setup, then repeatable runs for technical and non-technical users.

## What This Project Does

- Upscales large images using tiled Real-ESRGAN processing.
- Resizes images in pixels, cm, or inches.
- Compares original vs upscaled quality.
- Exports uncompressed image versions.
- Runs full workflows from a single config file.
- Commits and pushes code changes to GitHub with guided prompts.

## Who This Is For

- Non-technical users who want guided prompts.
- Technical users who want script-level control.
- Teams who want repeatable and shareable image workflows.

## Project Layout

```text
Image_resolution_using_agents/
  config.json                          # Main central configuration
  config_loader.py                     # Shared config/path resolver

  workflow_agent.py                    # Main orchestrator agent (task list executor)
  beginner_workflow_agent.py           # Guided non-technical runner
  github_sync_agent.py                 # Git commit/push assistant

  partition_and_upscale.py             # Tile split -> upscale -> merge pipeline
  image_resize.py                      # Resize utility
  image_quality_check.py               # Dimension and edge comparison
  uncompressed_image.py                # Export uncompressed image
  main.py                              # Image details and DPI helper

  .github/agents/                      # Custom Copilot agent definitions

  images/original/                     # Input images
  exe/realesrgan-ncnn-vulkan-.../      # Real-ESRGAN executable and models
```

## Quick Start (Step by Step)

### 1. Install prerequisites

Install these first:

- Python 3.9 or newer
- Git
- Real-ESRGAN executable folder (already included in this repo)

### 2. Open project folder in terminal

Run commands from project root.

Windows PowerShell example:

```powershell
cd D:\innovation\Image_resolution_using_agents
```

### 3. Install Python packages

```powershell
pip install pillow numpy matplotlib opencv-python
```

### 4. Update central config

Edit config.json and set paths for your files.

Minimum values to check:

- paths.input_image
- paths.upscaled_input_image
- paths.upscaled_output_image
- paths.realesrgan_exe

### 5. Run beginner mode (easiest)

```powershell
python beginner_workflow_agent.py --config config.json
```

You will be asked simple questions:

- preset (fast, balanced, quality)
- input image path
- output image path
- optional GitHub sync

### 6. Check outputs

- Upscaled output: from paths.upscaled_output_image
- Resized output: from resize.output_name in paths.resize_output_dir
- Uncompressed output: from paths.uncompressed_output (if task enabled)

## Full Workflow Mode

If you want deterministic runs from config only:

```powershell
python workflow_agent.py --config config.json
```

The run order comes from:

```json
"agent": {
  "tasks": ["upscale", "resize", "quality_check", "github_sync"]
}
```

## Individual Commands

Use these when you only want one operation:

```powershell
python partition_and_upscale.py --config config.json
python image_resize.py --config config.json
python image_quality_check.py --config config.json
python uncompressed_image.py --config config.json
python main.py --config config.json
python github_sync_agent.py
```

## Configuration Guide

### paths

- input_image: Source image for details/uncompressed conversion.
- upscaled_input_image: Input for tile upscaling.
- upscaled_output_image: Final merged upscaled output.
- resize_output_dir: Folder for resized images.
- uncompressed_output: Output path for uncompressed export.
- realesrgan_exe: Path to realesrgan-ncnn-vulkan.exe.

### upscale

- tile_size: Tile dimension. Larger can be faster but heavier memory usage.
- overlap: Blending overlap between tiles.
- merge_method: pil or numpy (pil is usually safer on RAM).
- model_name: Real-ESRGAN model name.
- scale: Upscale factor.

### resize

- unit: pixels, cm, or inches.
- width and height: target dimensions.
- dpi: used for cm/inches conversion.
- output_name: output filename.

### quality_check

- show_edges: true to visualize edge maps.

### git

- default_repo_link: optional default remote URL.
- visibility: private or public.

## Custom Agents Available

Custom agent files are under .github/agents.

- github-sync.agent.md
- beginner-workflow.agent.md
- image-quality-check.agent.md
- print-ready.agent.md
- large-image-upscale.agent.md
- uncompressed-export.agent.md

These agents are designed to make operations easier for non-technical users with guided behavior.

## GitHub Sync (Safe Workflow)

When github_sync_agent.py runs, it:

1. Asks for repository link.
2. Asks private/public visibility.
3. Asks commit message.
4. Adds and commits changes.
5. Validates/sets origin.
6. Pushes branch.

If a tracked file is above GitHub size limit (100 MB), push is blocked with a clear message.

## Recommended First-Time Git Setup

If not configured on your machine:

```powershell
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

Optional token for automatic repository creation in sync flow:

```powershell
$env:GITHUB_TOKEN="your_token_here"
```

## Troubleshooting (Step by Step)

### Issue: Push rejected due to file size

Reason: GitHub blocks files larger than 100 MB in normal git push.

Fix:

1. Remove file from tracking:
   git rm --cached <large_file_path>
2. Add that path to .gitignore
3. Commit again (or amend)
4. Push again

### Issue: "No changes to commit"

Reason: Working tree is already clean.

Fix:

1. Edit files you want to update.
2. Run sync again.

### Issue: Path not found

Fix:

1. Ensure you run commands from project root.
2. Use relative paths in config.json.
3. Verify exe and image paths exist.

### Issue: Upscaling fails mid-run

Fix:

1. Reduce upscale.tile_size in config.json.
2. Keep overlap moderate (16 to 48).
3. Retry with fast preset using beginner runner.

## Best Practices

- Keep generated outputs out of git unless needed.
- Prefer relative paths in config.json.
- Start with balanced preset, then tune quality.
- Use smaller tile_size on low-memory systems.
- Keep commit messages specific and short.

## Typical User Flows

### Flow A: Non-technical user

1. Run beginner_workflow_agent.py
2. Select preset and provide paths
3. Let workflow run automatically
4. Optionally sync to GitHub

### Flow B: Technical user

1. Edit config.json directly
2. Run workflow_agent.py
3. Run quality check
4. Sync code using github_sync_agent.py

## Notes

- This repository is currently optimized for Windows paths and PowerShell examples.
- Real-ESRGAN processing quality and speed depend on image type, model, and hardware.
