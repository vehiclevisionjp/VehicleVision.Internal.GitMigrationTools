#!/usr/bin/env python3
"""Generate icon for Git Migration Tool."""

from PIL import Image, ImageDraw


def generate_icon():
    """Generate a Git migration icon (branch with arrow)."""
    # Create a 256x256 image with transparent background
    size = 256
    icon = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(icon)

    # Git orange color
    git_orange = (241, 80, 47, 255)
    dark_gray = (50, 50, 50, 255)
    light_bg = (230, 240, 250, 255)

    # Draw light background circle
    padding = 20
    draw.ellipse(
        [(padding, padding), (size - padding, size - padding)],
        fill=light_bg,
        outline=git_orange,
        width=3,
    )

    # Draw branch-like shape (source)
    # Left circle (source repo)
    source_x, source_y = 60, 80
    draw.ellipse(
        [(source_x - 15, source_y - 15), (source_x + 15, source_y + 15)],
        fill=git_orange,
    )

    # Draw branch lines
    mid_y = 128
    # Vertical line from source
    draw.line([(source_x, source_y + 15), (source_x, mid_y)], fill=dark_gray, width=4)

    # Right circle (destination repo)
    dest_x, dest_y = 196, 80
    draw.ellipse(
        [(dest_x - 15, dest_y - 15), (dest_x + 15, dest_y + 15)],
        fill=git_orange,
    )

    # Horizontal line connecting at top
    draw.line([(source_x, mid_y), (dest_x, mid_y)], fill=dark_gray, width=4)

    # Arrow pointing right (migration direction)
    arrow_start_x = source_x + 50
    arrow_y = mid_y
    arrow_end_x = dest_x - 30

    # Arrow line
    draw.line(
        [(arrow_start_x, arrow_y), (arrow_end_x, arrow_y)], fill=git_orange, width=5
    )

    # Arrow head
    arrow_size = 12
    arrow_points = [
        (arrow_end_x, arrow_y),
        (arrow_end_x - arrow_size, arrow_y - arrow_size),
        (arrow_end_x - arrow_size, arrow_y + arrow_size),
    ]
    draw.polygon(arrow_points, fill=git_orange)

    # Vertical line down from destination
    dest_line_end = 200
    draw.line([(dest_x, dest_y + 15), (dest_x, dest_line_end)], fill=dark_gray, width=4)

    # Small circles at ends (connection points)
    for cx, cy in [(source_x, mid_y), (dest_x, mid_y)]:
        draw.ellipse(
            [(cx - 6, cy - 6), (cx + 6, cy + 6)],
            fill=git_orange,
        )

    # Save as PNG
    icon.save("assets/icon.png", "PNG")
    print("✓ Generated assets/icon.png")

    # Convert to ICO (create multiple sizes for proper ICO)
    # Generate icons at standard sizes: 16, 32, 64, 128, 256
    icon_sizes = [16, 32, 64, 128, 256]
    icon_images = [icon.resize((s, s), Image.Resampling.LANCZOS) for s in icon_sizes]

    # Save as ICO (using largest as primary)
    icon_images[4].save(
        "assets/icon.ico",
        "ICO",
        sizes=[(s, s) for s in icon_sizes],
    )
    print("✓ Generated assets/icon.ico")


if __name__ == "__main__":
    generate_icon()
