#!/bin/bash
set -e

# The directory we want to write to
STORAGE_DIR="/data/pdfs"

# Check if we're running as root (entrypoint starts as root)
if [[ $USER == "root" ]]; then
  echo "Container starting as root. Checking storage permissions..."
  
  # Ensure the storage directory exists
  mkdir -p "$STORAGE_DIR"

  # Get the current user ID (the non-root user we created in Dockerfile)
  # Since we're running as root, we look for the UID of 'mcpuser'
  TARGET_UID=$(id -u mcpuser)
  TARGET_GID=$(id -g mcpuser)

  # Check if the storage directory is owned by someone else
  # (e.g. from a bind mount or named volume)
  CURRENT_UID=$(stat -c '%u' "$STORAGE_DIR")

  if [[ "$CURRENT_UID" -ne "$TARGET_UID" ]]; then
    echo "Detected permission mismatch: $STORAGE_DIR is owned by UID $CURRENT_UID, but app needs UID $TARGET_UID"
    
    # If it's a bind mount, we can't easily change ownership without sudo
    # (which we don't have inside the container)
    # But we can try to change it if it's not a read-only mount
    if mount | grep "on $STORAGE_DIR " | grep -q "ro"; then
      echo "CRITICAL: $STORAGE_DIR is a READ-ONLY bind mount. Application will not be able to save PDFs."
      echo "Please remount with read-write access or use a named volume."
    else
      echo "Attempting to fix permissions..."
      chown -R mcpuser:mcpuser "$STORAGE_DIR"
      chmod -R 775 "$STORAGE_DIR"
      echo "Permissions updated successfully."
    fi
  else
    echo "$STORAGE_DIR is correctly owned by mcpuser. Ready to go."
  fi

  # Ensure the app directory is also owned by mcpuser
  chown -R mcpuser:mcpuser /app
  chmod -R 755 /app

  # Switch to the non-root user for the actual application
  exec gosu mcpuser "$@"
else
  # Already running as non-root
  exec "$@"
fi
