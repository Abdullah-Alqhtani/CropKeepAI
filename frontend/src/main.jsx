/*
 * Browser entry point for the React application.
 * It mounts the top-level App component into the HTML element created by Vite.
 */
import React from 'react';
import { createRoot } from 'react-dom/client';
import { App } from './App.jsx';
import './styles.css';

// StrictMode helps reveal unsafe React patterns during development.
createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
