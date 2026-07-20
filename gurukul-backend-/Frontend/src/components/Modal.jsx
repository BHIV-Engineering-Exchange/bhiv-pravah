import React, { useState, useEffect, useRef } from 'react';
import { FaTimes, FaExclamationTriangle, FaCheckCircle, FaInfoCircle, FaTrash } from 'react-icons/fa';

const Modal = ({ isOpen, onClose, type = 'alert', title, message, onConfirm, onCancel, confirmText = 'OK', cancelText = 'Cancel', placeholder = '' }) => {
    const [inputValue, setInputValue] = useState('');
    const inputRef = useRef(null);

    useEffect(() => {
        if (isOpen && type === 'prompt' && inputRef.current) {
            inputRef.current.focus();
        }
    }, [isOpen, type]);

    useEffect(() => {
        if (isOpen) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = 'unset';
        }
        return () => {
            document.body.style.overflow = 'unset';
        };
    }, [isOpen]);

    if (!isOpen) return null;

    const handleConfirm = () => {
        if (type === 'prompt') {
            if (onConfirm) {
                onConfirm(inputValue);
            }
        } else {
            if (onConfirm) {
                onConfirm();
            }
        }
        setInputValue('');
    };

    const handleCancel = () => {
        if (onCancel) {
            onCancel();
        }
        setInputValue('');
        onClose();
    };

    const getIcon = () => {
        switch (type) {
            case 'confirm':
            case 'delete':
                return <FaExclamationTriangle className="text-orange-400" />;
            case 'success':
                return <FaCheckCircle className="text-green-400" />;
            case 'error':
                return <FaExclamationTriangle className="text-red-400" />;
            case 'prompt':
                return <FaInfoCircle className="text-blue-400" />;
            default:
                return <FaInfoCircle className="text-orange-400" />;
        }
    };

    const getButtonColors = () => {
        switch (type) {
            case 'delete':
                return {
                    confirm: 'bg-red-600 hover:bg-red-500 text-white',
                    cancel: 'bg-white/10 hover:bg-white/20 text-gray-300'
                };
            case 'confirm':
                return {
                    confirm: 'bg-orange-600 hover:bg-orange-500 text-white',
                    cancel: 'bg-white/10 hover:bg-white/20 text-gray-300'
                };
            case 'success':
                return {
                    confirm: 'bg-green-600 hover:bg-green-500 text-white',
                    cancel: 'bg-white/10 hover:bg-white/20 text-gray-300'
                };
            case 'error':
                return {
                    confirm: 'bg-red-600 hover:bg-red-500 text-white',
                    cancel: 'bg-white/10 hover:bg-white/20 text-gray-300'
                };
            default:
                return {
                    confirm: 'bg-orange-600 hover:bg-orange-500 text-white',
                    cancel: 'bg-white/10 hover:bg-white/20 text-gray-300'
                };
        }
    };

    const buttonColors = getButtonColors();

    return (
        <div className="fixed inset-0 z-[99999] flex items-center justify-center p-4">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/80 backdrop-blur-sm animate-fade-in"
                onClick={type === 'alert' ? handleConfirm : undefined}
            />

            {/* Modal */}
            <div className="relative glass-panel border border-white/20 rounded-3xl shadow-2xl max-w-md w-full animate-fade-in-up p-6 sm:p-8 z-10">
                {/* Close Button (only for non-alert types) */}
                {type !== 'alert' && (
                    <button
                        onClick={handleCancel}
                        className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors p-2 hover:bg-white/10 rounded-lg"
                    >
                        <FaTimes />
                    </button>
                )}

                {/* Icon */}
                <div className="flex justify-center mb-4">
                    <div className="w-16 h-16 rounded-full bg-white/10 flex items-center justify-center text-3xl border-2 border-white/20">
                        {getIcon()}
                    </div>
                </div>

                {/* Title */}
                {title && (
                    <h2 className="text-2xl font-bold text-white text-center mb-3">
                        {title}
                    </h2>
                )}

                {/* Message */}
                <p className="text-gray-300 text-center mb-6 leading-relaxed">
                    {message}
                </p>

                {/* Input (for prompt type) */}
                {type === 'prompt' && (
                    <div className="mb-6">
                        <input
                            ref={inputRef}
                            type="text"
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter') {
                                    handleConfirm();
                                } else if (e.key === 'Escape') {
                                    handleCancel();
                                }
                            }}
                            placeholder={placeholder}
                            className="w-full bg-black/40 border border-white/10 rounded-xl p-3 text-white focus:border-orange-500 focus:outline-none transition-colors"
                            autoFocus
                        />
                    </div>
                )}

                {/* Buttons */}
                <div className={`flex gap-3 ${type === 'alert' ? 'justify-center' : 'justify-end'}`}>
                    {type !== 'alert' && (
                        <button
                            onClick={handleCancel}
                            className={`px-6 py-2.5 rounded-xl font-medium transition-all ${buttonColors.cancel}`}
                        >
                            {cancelText}
                        </button>
                    )}
                    <button
                        onClick={handleConfirm}
                        className={`px-6 py-2.5 rounded-xl font-medium transition-all shadow-lg ${buttonColors.confirm}`}
                    >
                        {confirmText}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Modal;

