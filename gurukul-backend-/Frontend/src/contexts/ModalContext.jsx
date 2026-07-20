import React, { createContext, useContext, useState } from 'react';
import Modal from '../components/Modal';

const ModalContext = createContext();

export const useModal = () => {
    const context = useContext(ModalContext);
    if (!context) {
        throw new Error('useModal must be used within ModalProvider');
    }
    return context;
};

export const ModalProvider = ({ children }) => {
    const [modal, setModal] = useState({
        isOpen: false,
        type: 'alert',
        title: '',
        message: '',
        confirmText: 'OK',
        cancelText: 'Cancel',
        placeholder: '',
        onConfirm: null,
        onCancel: null
    });

    const showModal = (config) => {
        return new Promise((resolve) => {
            setModal({
                isOpen: true,
                type: config.type || 'alert',
                title: config.title || '',
                message: config.message || '',
                confirmText: config.confirmText || 'OK',
                cancelText: config.cancelText || 'Cancel',
                placeholder: config.placeholder || '',
                onConfirm: () => {
                    setModal(prev => ({ ...prev, isOpen: false }));
                    resolve(true);
                    if (config.onConfirm) config.onConfirm();
                },
                onCancel: () => {
                    setModal(prev => ({ ...prev, isOpen: false }));
                    resolve(false);
                    if (config.onCancel) config.onCancel();
                }
            });
        });
    };

    const alert = (message, title = 'Alert') => {
        return showModal({ type: 'alert', title, message });
    };

    const confirm = (message, title = 'Confirm') => {
        return showModal({
            type: 'confirm',
            title,
            message,
            confirmText: 'Confirm',
            cancelText: 'Cancel'
        });
    };

    const prompt = (message, title = 'Input Required', placeholder = '') => {
        return new Promise((resolve) => {
            setModal({
                isOpen: true,
                type: 'prompt',
                title,
                message,
                placeholder,
                confirmText: 'Submit',
                cancelText: 'Cancel',
                onConfirm: (value) => {
                    setModal(prev => ({ ...prev, isOpen: false }));
                    resolve(value || '');
                },
                onCancel: () => {
                    setModal(prev => ({ ...prev, isOpen: false }));
                    resolve(null);
                }
            });
        });
    };

    const success = (message, title = 'Success') => {
        return showModal({ type: 'success', title, message });
    };

    const error = (message, title = 'Error') => {
        return showModal({ type: 'error', title, message });
    };

    const deleteConfirm = (message, title = 'Delete Confirmation') => {
        return showModal({
            type: 'delete',
            title,
            message,
            confirmText: 'Delete',
            cancelText: 'Cancel'
        });
    };

    const closeModal = () => {
        setModal(prev => ({ ...prev, isOpen: false }));
    };

    return (
        <ModalContext.Provider value={{ alert, confirm, prompt, success, error, deleteConfirm, closeModal }}>
            {children}
            <Modal
                isOpen={modal.isOpen}
                onClose={closeModal}
                type={modal.type}
                title={modal.title}
                message={modal.message}
                onConfirm={modal.onConfirm}
                onCancel={modal.onCancel}
                confirmText={modal.confirmText}
                cancelText={modal.cancelText}
                placeholder={modal.placeholder}
            />
        </ModalContext.Provider>
    );
};

