/* eslint-disable react-refresh/only-export-components */
import {createContext, useContext, useState, useEffect} from 'react';
import {initUser} from "../services/api";

const AppContext = createContext(null);

export function AppProvider({ children })
{
    const [username, setUsernameState]= useState(()=> localStorage.getItem("username")|| "");
    const [courseCode, setCourseCodeState]= useState(()=> localStorage.getItem("courseCode")|| "");

    const setUsername=(val)=>{
        setUsernameState(val);
        localStorage.setItem("username", val);
    };
    const setCourseCode = (val) => {
    const upper = val.toUpperCase().trim();
    setCourseCodeState(upper);
    localStorage.setItem("courseCode", upper);
  };
  useEffect(()=>{
    if(username && courseCode){
      initUser(username, courseCode).catch(()=>{});
    }
  }, [username, courseCode]);

    return (
        <AppContext.Provider value={{username, setUsername, courseCode, setCourseCode}}>
            { children }
        </AppContext.Provider>
    );
}
export const useApp= ()=> useContext(AppContext);