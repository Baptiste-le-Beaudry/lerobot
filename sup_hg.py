from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="Baptiste-le-Beaudry/act_lekiwi_full",
    force_download=True,
    local_dir_use_symlinks=False
)
