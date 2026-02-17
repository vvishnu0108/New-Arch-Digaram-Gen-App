import { Download, FileImage, FileCode, FileText } from 'lucide-react';
import { diagramsApi } from '../services/api';
import './DownloadControls.css';

/**
 * Download buttons for various file formats
 */
function DownloadControls({ files = [] }) {
    if (files.length === 0) {
        return null;
    }

    const getIcon = (format) => {
        switch (format) {
            case 'png':
                return <FileImage size={14} />;
            case 'dot':
                return <FileCode size={14} />;
            case 'drawio':
                return <FileText size={14} />;
            default:
                return <Download size={14} />;
        }
    };

    const getLabel = (format) => {
        switch (format) {
            case 'png':
                return 'PNG Image';
            case 'dot':
                return 'DOT File';
            case 'drawio':
                return 'Draw.IO';
            default:
                return format.toUpperCase();
        }
    };

    const handleDownload = async (file) => {
        try {
            const url = diagramsApi.getFileUrl(file.filename);
            const response = await fetch(url);
            const blob = await response.blob();

            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = file.filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(link.href);
        } catch (error) {
            console.error('Download failed:', error);
        }
    };

    return (
        <div className="download-controls">
            <span className="download-label">
                <Download size={14} />
                Downloads
            </span>
            <div className="download-buttons">
                {files.map((file) => (
                    <button
                        key={file.format}
                        className="btn btn-secondary btn-sm"
                        onClick={() => handleDownload(file)}
                        title={`Download ${getLabel(file.format)}`}
                    >
                        {getIcon(file.format)}
                        {getLabel(file.format)}
                    </button>
                ))}
            </div>
        </div>
    );
}

export default DownloadControls;
