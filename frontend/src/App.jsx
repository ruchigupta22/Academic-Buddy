import {BrowserRouter, Routes, Route} from 'react-router-dom';
import {Toaster} from "react-hot-toast";
import { AppProvider } from "./context/AppContext";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Chat      from "./pages/Chat";
import Quiz      from "./pages/Quiz";
import Revision  from "./pages/Revision";
import PYQ       from "./pages/PYQ";

export default function App(){
  return(
    <AppProvider>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/"         element={<Dashboard />} />
            <Route path="/chat"     element={<Chat />} />
            <Route path="/quiz"     element={<Quiz />} />
            <Route path="/revision" element={<Revision />} />
            <Route path="/pyq"      element={<PYQ />} />
          </Routes>
        </Layout>
      </BrowserRouter>
      <Toaster position="top-right" 
      toastOptions={{
        className: "toast",
        duration: 3000,
      }}
      />
    </AppProvider>
  );
}