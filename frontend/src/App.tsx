import { BrowserRouter, Routes, Route } from 'react-router-dom';
import TopNav from './components/TopNav';
import Dashboard from './pages/Dashboard';
import ActiveTickets from './pages/ActiveTickets';
import Bottlenecks from './pages/Bottlenecks';
import './index.css';

function App() {
  return (
    <BrowserRouter>
      {/* Ambient background orbs */}
      <div className="ambient-orbs">
        <div className="orb-1" />
        <div className="orb-2" />
      </div>

      <TopNav />

      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/active-tickets" element={<ActiveTickets />} />
        <Route path="/bottlenecks" element={<Bottlenecks />} />
        {/* Talent routing can be opened from any page via modal */}
        <Route path="/talent-routing/:ticketId" element={<ActiveTickets />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
