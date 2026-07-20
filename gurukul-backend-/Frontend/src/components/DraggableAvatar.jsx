import React, { useState, useEffect, useRef } from 'react';
import AvatarChatbot from './AvatarChatbot';

const DraggableAvatar = () => {
    const [image, setImage] = useState(null);
    const [settings, setSettings] = useState({
        position: { x: 0, y: 0.5, z: -4 },
        rotation: { x: 0, y: 180, z: 0 },
        scale: 0.6,
        pinMode: true
    });
    const [dragPosition, setDragPosition] = useState({ x: window.innerWidth - 150, y: 100 });
    const [isDragging, setIsDragging] = useState(false);
    const [isChatOpen, setIsChatOpen] = useState(false);
    const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
    const [clickStart, setClickStart] = useState({ x: 0, y: 0 });

    useEffect(() => {
        // Load from localStorage
        const loadSettings = () => {
            const savedImage = localStorage.getItem('avatarImage');
            setImage(savedImage);

            setSettings({
                position: JSON.parse(localStorage.getItem('avatarPosition') || '{"x":0,"y":0.5,"z":-4}'),
                rotation: JSON.parse(localStorage.getItem('avatarRotation') || '{"x":0,"y":180,"z":0}'),
                scale: parseFloat(localStorage.getItem('avatarScale') || '0.6'),
                pinMode: JSON.parse(localStorage.getItem('avatarPinMode') || 'true')
            });

            const savedDragPos = localStorage.getItem('avatarDragPosition');
            if (savedDragPos) {
                setDragPosition(JSON.parse(savedDragPos));
            }
        };

        loadSettings();

        // Listen for storage changes from Avatar page
        window.addEventListener('storage', loadSettings);

        // Custom event for same-window updates
        const handleAvatarUpdate = () => loadSettings();
        window.addEventListener('avatarUpdate', handleAvatarUpdate);

        return () => {
            window.removeEventListener('storage', loadSettings);
            window.removeEventListener('avatarUpdate', handleAvatarUpdate);
        };
    }, []);

    const handleStart = (e) => {
        if (settings.pinMode) return; // Can't drag in pin mode

        const clientX = e.touches ? e.touches[0].clientX : e.clientX;
        const clientY = e.touches ? e.touches[0].clientY : e.clientY;

        setIsDragging(true);
        setClickStart({ x: clientX, y: clientY });
        setDragStart({
            x: clientX - dragPosition.x,
            y: clientY - dragPosition.y
        });
        e.preventDefault();
    };

    const handleMove = (e) => {
        if (isDragging && !settings.pinMode) {
            const clientX = e.touches ? e.touches[0].clientX : e.clientX;
            const clientY = e.touches ? e.touches[0].clientY : e.clientY;

            const newX = clientX - dragStart.x;
            const newY = clientY - dragStart.y;

            // Keep within viewport bounds
            const avatarSize = 128 * settings.scale;
            const maxX = window.innerWidth - avatarSize;
            const maxY = window.innerHeight - avatarSize;

            setDragPosition({
                x: Math.max(0, Math.min(newX, maxX)),
                y: Math.max(0, Math.min(newY, maxY))
            });
        }
    };

    const handleEnd = (e) => {
        if (isDragging) {
            const clientX = e.changedTouches ? e.changedTouches[0].clientX : e.clientX;
            const clientY = e.changedTouches ? e.changedTouches[0].clientY : e.clientY;

            setIsDragging(false);

            // Save drag position
            localStorage.setItem('avatarDragPosition', JSON.stringify(dragPosition));

            // Check if it was a click/tap (< 5px movement)
            const distance = Math.sqrt(
                Math.pow(clientX - clickStart.x, 2) +
                Math.pow(clientY - clickStart.y, 2)
            );

            if (distance < 5) {
                setIsChatOpen(!isChatOpen);
            }
        }
    };

    useEffect(() => {
        if (isDragging) {
            window.addEventListener('mousemove', handleMove);
            window.addEventListener('mouseup', handleEnd);
            window.addEventListener('touchmove', handleMove, { passive: false });
            window.addEventListener('touchend', handleEnd);
            return () => {
                window.removeEventListener('mousemove', handleMove);
                window.removeEventListener('mouseup', handleEnd);
                window.removeEventListener('touchmove', handleMove);
                window.removeEventListener('touchend', handleEnd);
            };
        }
    }, [isDragging]);

    // Don't render if no image uploaded (AFTER all hooks)
    if (!image) return null;

    // Calculate transform based on settings
    const transform = `
        translate(${dragPosition.x}px, ${dragPosition.y}px)
        rotateX(${settings.rotation.x}deg)
        rotateY(${settings.rotation.y}deg)
        rotateZ(${settings.rotation.z}deg)
        scale(${settings.scale})
    `;

    return (
        <>
            <div
                onMouseDown={handleStart}
                onTouchStart={handleStart}
                style={{
                    position: 'fixed',
                    left: 0,
                    top: 0,
                    transform,
                    cursor: settings.pinMode ? 'default' : (isDragging ? 'grabbing' : 'grab'),
                    zIndex: 9999,
                    transformOrigin: 'center',
                    transition: isDragging ? 'none' : 'transform 0.3s ease',
                    userSelect: 'none',
                    touchAction: 'none'
                }}
                className="w-24 h-24 sm:w-32 sm:h-32 rounded-full shadow-2xl overflow-hidden hover:scale-110 transition-transform"
            >
                <img
                    src={image}
                    alt="Avatar"
                    className="w-full h-full object-cover pointer-events-none"
                    draggable="false"
                />
            </div>

            {isChatOpen && (
                <AvatarChatbot
                    position={dragPosition}
                    onClose={() => setIsChatOpen(false)}
                />
            )}
        </>
    );
};

export default DraggableAvatar;
