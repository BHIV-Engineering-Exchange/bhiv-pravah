import React, { useState, useEffect, useRef } from 'react';
import Sidebar from '../components/Sidebar';
import { FaUpload, FaTrash, FaRedo, FaInfoCircle, FaChevronUp, FaChevronDown } from 'react-icons/fa';
import { useKarma } from '../contexts/KarmaContext';
import { useModal } from '../contexts/ModalContext';

const ControlInput = ({ label, value, onChange, unit = "" }) => {
    const handleIncrement = () => onChange(Number((value + 0.1).toFixed(1)));
    const handleDecrement = () => onChange(Number((value - 0.1).toFixed(1)));
    const handleChange = (e) => onChange(Number(e.target.value));

    return (
        <div className="bg-black/70 rounded-xl p-2.5 border border-white/5 focus-within:border-orange-500/50 focus-within:bg-black/60 transition-all duration-300 group relative flex justify-between items-center h-[72px]">
            <div className="flex flex-col justify-center h-full w-full mr-2">
                <span className="text-[10px] text-gray-300 font-bold uppercase tracking-widest block mb-0.5 group-focus-within:text-orange-400 transition-colors">{label}</span>
                <div className="flex items-baseline gap-0.5">
                    <input
                        type="number"
                        value={value}
                        onChange={handleChange}
                        step="0.1"
                        className="w-full bg-transparent text-white text-lg font-bold outline-none font-mono tracking-tight appearance-none [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none [-moz-appearance:textfield]"
                    />
                    {unit && <span className="text-gray-500 text-xs font-medium">{unit}</span>}
                </div>
            </div>

            <div className="flex flex-col gap-1">
                <button
                    onClick={handleIncrement}
                    className="w-5 h-5 flex items-center justify-center bg-white/5 hover:bg-orange-500/20 rounded text-gray-400 hover:text-orange-400 transition-colors cursor-pointer active:scale-95"
                >
                    <FaChevronUp size={8} />
                </button>
                <button
                    onClick={handleDecrement}
                    className="w-5 h-5 flex items-center justify-center bg-white/5 hover:bg-orange-500/20 rounded text-gray-400 hover:text-orange-400 transition-colors cursor-pointer active:scale-95"
                >
                    <FaChevronDown size={8} />
                </button>
            </div>
        </div>
    );
};

const Avatar = () => {
    const fileInputRef = useRef(null);
    const { alert, confirm } = useModal();

    // Load from localStorage or use defaults
    const [uploadedImage, setUploadedImage] = useState(() =>
        localStorage.getItem('avatarImage') || null
    );
    const [position, setPosition] = useState(() => {
        const saved = localStorage.getItem('avatarDragPosition');
        return saved ? JSON.parse(saved) : { x: window.innerWidth - 150, y: 100 };
    });
    const [rotation, setRotation] = useState(() => {
        const saved = localStorage.getItem('avatarRotation');
        return saved ? JSON.parse(saved) : { x: 0, y: 180, z: 0 };
    });
    const [scale, setScale] = useState(() => {
        const saved = localStorage.getItem('avatarScale');
        return saved ? parseFloat(saved) : 0.6;
    });
    const [pinMode, setPinMode] = useState(() => {
        const saved = localStorage.getItem('avatarPinMode');
        return saved ? JSON.parse(saved) : true;
    });

    // Save to localStorage whenever values change
    useEffect(() => {
        localStorage.setItem('avatarDragPosition', JSON.stringify(position));
        window.dispatchEvent(new Event('avatarUpdate'));
    }, [position]);

    useEffect(() => {
        localStorage.setItem('avatarRotation', JSON.stringify(rotation));
        window.dispatchEvent(new Event('avatarUpdate'));
    }, [rotation]);

    useEffect(() => {
        localStorage.setItem('avatarScale', scale.toString());
        window.dispatchEvent(new Event('avatarUpdate'));
    }, [scale]);

    useEffect(() => {
        localStorage.setItem('avatarPinMode', JSON.stringify(pinMode));
        window.dispatchEvent(new Event('avatarUpdate'));
    }, [pinMode]);

    const handleImageUpload = (e) => {
        const file = e.target.files[0];
        if (!file) return;

        if (!file.type.startsWith('image/')) {
            alert('Please upload an image file', 'Invalid File Type');
            return;
        }

        if (file.size > 5 * 1024 * 1024) {
            alert('Image must be less than 5MB', 'File Too Large');
            return;
        }

        const reader = new FileReader();
        reader.onloadend = () => {
            const imageData = reader.result;

            setUploadedImage(imageData);
            localStorage.setItem('avatarImage', imageData);
            window.dispatchEvent(new Event('avatarUpdate'));
        };
        reader.readAsDataURL(file);
    };

    const handleRemoveImage = async (e) => {
        e?.stopPropagation();
        e?.preventDefault();
        
        const result = await confirm('Are you sure you want to remove this avatar?', 'Remove Avatar');
        if (result) {
            setUploadedImage(null);
            localStorage.removeItem('avatarImage');
            window.dispatchEvent(new Event('avatarUpdate'));
        }
    };

    const handleReset = () => {
        setPosition({ x: window.innerWidth - 150, y: 100 });
        setRotation({ x: 0, y: 180, z: 0 });
        setScale(0.6);
        setPinMode(true);
    };

    return (
        <div className="flex pt-20 sm:pt-24 min-h-screen container mx-auto px-2 sm:px-4 gap-3 sm:gap-6">
            <Sidebar />

            <main className="flex-grow flex flex-col lg:flex-row gap-4 sm:gap-6 animate-fade-in-up" style={{ animationDelay: '0.2s' }}>

                {/* Main Content: Avatar Grid */}
                <div className="flex-grow glass-panel no-hover p-4 md:p-8 rounded-3xl border border-white/10 flex flex-col shadow-2xl relative overflow-hidden">
                    {/* Background Glow */}
                    <div className="absolute top-0 right-0 w-96 h-96 bg-orange-500/10 rounded-full blur-3xl pointer-events-none -translate-y-1/2 translate-x-1/2"></div>

                    {/* Header */}
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 sm:mb-8 relative z-10 gap-3 sm:gap-4">
                        <div>
                            <h1 className="text-xl sm:text-2xl md:text-3xl font-bold text-white mb-2">Avatar Management</h1>
                            <p className="text-gray-300 text-xs sm:text-sm">Upload and customize your draggable avatar</p>
                        </div>
                        <div className="flex gap-3 w-full md:w-auto">
                            <input
                                ref={fileInputRef}
                                type="file"
                                accept="image/*"
                                onChange={handleImageUpload}
                                className="hidden"
                            />
                            <button
                                onClick={() => fileInputRef.current?.click()}
                                className="flex-1 md:flex-none flex items-center justify-center gap-2 px-6 py-2.5 bg-orange-600 hover:bg-orange-500 text-white rounded-xl transition-all border border-orange-500 font-medium shadow-lg shadow-orange-500/20"
                            >
                                <FaUpload className="text-sm" />
                                Upload Image
                            </button>
                        </div>
                    </div>

                    {/* Preview Section */}
                    <div className="flex-grow flex flex-col relative z-10">
                        <div className="flex justify-between items-center mb-6">
                            <h2 className="text-xl font-semibold text-white">Avatar Preview</h2>
                            {uploadedImage && (
                                <button
                                    onClick={handleRemoveImage}
                                    type="button"
                                    className="text-red-400 hover:text-red-300 text-xs border border-red-500/30 hover:border-red-500/50 px-3 py-1.5 rounded-lg transition-all bg-red-500/10 flex items-center gap-2"
                                >
                                    <FaTrash size={12} />
                                    Remove Image
                                </button>
                            )}
                        </div>

                        {/* Avatar Preview */}
                        <div className="flex items-center justify-center p-6 md:p-12 bg-black/40 rounded-2xl border border-white/10">
                            {uploadedImage ? (
                                <div
                                    className="relative rounded-full shadow-2xl border-4 border-orange-500 overflow-hidden"
                                    style={{
                                        width: `${128 * scale}px`,
                                        height: `${128 * scale}px`,
                                        transform: `rotateX(${rotation.x}deg) rotateY(${rotation.y}deg) rotateZ(${rotation.z}deg)`
                                    }}
                                >
                                    <img
                                        src={uploadedImage}
                                        alt="Avatar Preview"
                                        className="w-full h-full object-cover"
                                    />
                                </div>
                            ) : (
                                <div className="text-center">
                                    <FaUpload className="text-6xl text-gray-600 mx-auto mb-4" />
                                    <p className="text-gray-400 text-lg">No avatar uploaded</p>
                                    <p className="text-gray-500 text-sm mt-2">Click "Upload Image" to get started</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Right Panel: Settings */}
                <div className="w-full lg:w-80 glass-panel no-hover p-4 sm:p-6 rounded-3xl border border-white/10 flex flex-col shadow-2xl h-fit">
                    <h2 className="text-lg sm:text-xl font-bold text-white mb-4 sm:mb-6">Avatar Settings</h2>

                    {/* Pin Mode Toggle */}
                    <div className="flex justify-between items-center mb-8 p-3 rounded-xl bg-black/60 border border-white/10">
                        <span className="text-white font-medium">Pin Mode</span>
                        <div
                            className={`w-12 h-6 rounded-full p-1 cursor-pointer transition-colors duration-300 ${pinMode ? 'bg-orange-500' : 'bg-gray-600'} `}
                            onClick={() => setPinMode(!pinMode)}
                        >
                            <div className={`w-4 h-4 bg-white rounded-full shadow-md transform transition-transform duration-300 ${pinMode ? 'translate-x-6' : 'translate-x-0'} `}></div>
                        </div>
                    </div>

                    {/* Pin Position */}
                    <div className="mb-6">
                        <label className="text-orange-200 text-xs font-bold uppercase tracking-wider mb-3 block">Pin Position</label>
                        <div className="grid grid-cols-2 gap-2">
                            <ControlInput
                                label="X"
                                value={position.x}
                                onChange={(val) => setPosition({ ...position, x: val })}
                            />
                            <ControlInput
                                label="Y"
                                value={position.y}
                                onChange={(val) => setPosition({ ...position, y: val })}
                            />
                        </div>
                    </div>

                    {/* Pin Rotation */}
                    <div className="mb-6">
                        <label className="text-orange-200 text-xs font-bold uppercase tracking-wider mb-3 block">Pin Rotation</label>
                        <div className="grid grid-cols-3 gap-2">
                            <ControlInput
                                label="X"
                                value={rotation.x}
                                onChange={(val) => setRotation({ ...rotation, x: val })}
                                unit="°"
                            />
                            <ControlInput
                                label="Y"
                                value={rotation.y}
                                onChange={(val) => setRotation({ ...rotation, y: val })}
                                unit="°"
                            />
                            <ControlInput
                                label="Z"
                                value={rotation.z}
                                onChange={(val) => setRotation({ ...rotation, z: val })}
                                unit="°"
                            />
                        </div>
                    </div>

                    {/* Pin Scale */}
                    <div className="mb-8">
                        <label className="text-orange-200 text-xs font-bold uppercase tracking-wider mb-3 block">Pin Scale</label>
                        <div className="bg-black/70 rounded-xl p-3 border border-white/5 focus-within:border-orange-500/50 focus-within:bg-black/60 transition-all duration-300 group relative">
                            <span className="text-[10px] text-gray-300 font-bold uppercase tracking-widest block mb-1 group-focus-within:text-orange-400 transition-colors">Size</span>
                            <div className="flex items-center gap-4">
                                <input
                                    type="range"
                                    min="0.1"
                                    max="2.0"
                                    step="0.1"
                                    value={scale}
                                    onChange={(e) => setScale(parseFloat(e.target.value))}
                                    className="flex-grow h-1 bg-white/10 rounded-lg appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:bg-orange-500 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:transition-transform hover:[&::-webkit-slider-thumb]:scale-125"
                                />
                                <span className="font-mono text-white text-lg font-bold w-12 text-right">{scale.toFixed(1)}</span>
                            </div>
                        </div>
                    </div>

                    {/* Reset Button */}
                    <button
                        onClick={handleReset}
                        className="w-full mb-6 bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 py-3 rounded-lg flex items-center justify-center gap-2 transition-colors font-medium"
                    >
                        <FaRedo /> Reset Settings
                    </button>

                    {/* Tips Section */}
                    <div className="bg-orange-500/10 rounded-xl p-4 border border-orange-500/20">
                        <div className="flex items-center gap-2 mb-3 text-orange-200">
                            <FaInfoCircle className="text-sm" />
                            <span className="text-sm font-bold uppercase">Avatar Tips</span>
                        </div>
                        <ul className="text-sm text-gray-200 space-y-2 leading-relaxed list-disc pl-4 font-medium">
                            <li>Upload an image to see it on all pages</li>
                            <li>Adjust rotation to change orientation</li>
                            <li>Scale controls the size</li>
                            <li>Turn OFF Pin Mode to drag avatar around</li>
                            <li>Click avatar to open chatbot assistant</li>
                        </ul>
                    </div>

                </div>
            </main>
        </div>
    );
};

export default Avatar;
