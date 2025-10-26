import cv2
import numpy as np

def get_rotated_bbox(mask):
    """Calculate the minimum area rotated bounding box from a binary mask.
    
    Args:
        mask (numpy.ndarray): Binary mask where True/1 indicates the object region
        
    Returns:
        tuple: (center, (width, height), angle) where:
            - center: (x, y) coordinates of the box center
            - (width, height): dimensions of the box
            - angle: rotation angle in degrees, defined as:
                * Angle between the width edge and x-axis (horizontal line)
                * In OpenCV's coordinate system:
                    - Origin (0,0) is at top-left corner
                    - x-axis points right
                    - y-axis points down
                * Range: [-90, 0) or [0, 90)
                * Positive direction is counter-clockwise
                * OpenCV always returns the angle with smallest absolute value
                * Examples:
                    - 0°: width edge parallel to x-axis, pointing right
                    - 45°: width edge rotated 45° counter-clockwise
                    - -45°: width edge rotated 45° clockwise
    """
    # Find contours in the mask
    contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return None
        
    # Get the largest contour
    largest_contour = max(contours, key=cv2.contourArea)
    
    # Get the minimum area rectangle
    rect = cv2.minAreaRect(largest_contour)
    
    return rect

def get_rotated_bbox_corners(rect):
    """Get the four corners of a rotated bounding box.
    
    Args:
        rect: The rotated rectangle returned by get_rotated_bbox
        
    Returns:
        numpy.ndarray: Array of shape (4, 2) containing the coordinates of the four corners
    """
    if rect is None:
        return None
        
    box = cv2.boxPoints(rect)
    return np.int0(box)

def draw_rotated_bbox(image, rect, color=(0, 255, 0), thickness=2, show_angle=False):
    """Draw a rotated bounding box on an image.
    
    Args:
        image (numpy.ndarray): The image to draw on
        rect: The rotated rectangle returned by get_rotated_bbox
        color (tuple): BGR color tuple
        thickness (int): Line thickness
        show_angle (bool): Whether to show the angle information
        
    Returns:
        numpy.ndarray: Image with the rotated bounding box drawn
    """
    if rect is None:
        return image
        
    box = get_rotated_bbox_corners(rect)
    cv2.drawContours(image, [box], 0, color, thickness)
    
    if show_angle:
        # Draw center point
        center = rect[0]
        cv2.circle(image, (int(center[0]), int(center[1])), 3, (0, 0, 255), -1)
        
        # Draw width edge with angle
        width = rect[1][0]
        height = rect[1][1]
        angle = rect[2]
        
        # Calculate the direction vector of the width edge
        rad = np.deg2rad(angle)
        dx = np.cos(rad) * width/2
        dy = np.sin(rad) * width/2
        
        # Draw the width edge
        pt1 = (int(center[0] - dx), int(center[1] - dy))
        pt2 = (int(center[0] + dx), int(center[1] + dy))
        cv2.line(image, pt1, pt2, (255, 0, 0), 2)
        
        # Add angle text
        text = f"Angle: {angle:.1f}°"
        cv2.putText(image, text, (int(center[0] + 10), int(center[1] + 10)),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    
    return image
