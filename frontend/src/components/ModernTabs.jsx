import { LayoutGrid, FileText, Code2, CheckSquare } from 'lucide-react';
import './ModernTabs.css';

function ModernTabs({ activeTab, onTabChange, tabs = [] }) {
  const defaultTabs = [
    { id: 'diagram', label: 'Diagram', icon: LayoutGrid },
    { id: 'docs', label: 'Documentation', icon: FileText },
    { id: 'code', label: 'Code', icon: Code2 },
    { id: 'validation', label: 'Quality', icon: CheckSquare }
  ];

  const tabsToRender = tabs.length > 0 ? tabs : defaultTabs;

  return (
    <div className="modern-tabs">
      <div className="tabs-container">
        {tabsToRender.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              className={`tab ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => onTabChange(tab.id)}
            >
              {Icon && <Icon size={18} />}
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default ModernTabs;
