import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import api from "../services/api";

export interface SchoolSettings {
    school_name: string;
    motto: string | null;
    logo_url: string | null;
    current_term: string | null;
    current_academic_year: string | null;
}

interface SettingsContextType {
    settings: SchoolSettings;
    isLoading: boolean;
    error: string | null;
    refreshSettings: () => void;
}

const defaultSettings: SchoolSettings = {
    school_name: "School ERP",
    motto: null,
    logo_url: null,
    current_term: null,
    current_academic_year: null,
};

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

export const SettingsProvider = ({ children }: { children: ReactNode }) => {
    const [settings, setSettings] = useState<SchoolSettings>(defaultSettings);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchSettings = async () => {
        setIsLoading(true);
        try {
            const response = await api.get("/settings/");
            setSettings(response.data);
            localStorage.setItem("school_name", response.data.school_name);
            setError(null);
        } catch (err) {
            console.error("Failed to load school settings:", err);
            // Fallback for development if backend isn't ready
            const fallback = {
                school_name: "Demo High School",
                motto: "Striving for Excellence",
                logo_url: null,
                current_term: "Term 1",
                current_academic_year: "2026"
            };
            setSettings(fallback);
            localStorage.setItem("school_name", fallback.school_name);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchSettings();
    }, []);

    return (
        <SettingsContext.Provider value={{ settings, isLoading, error, refreshSettings: fetchSettings }}>
            {children}
        </SettingsContext.Provider>
    );
};

export const useSettings = () => {
    const context = useContext(SettingsContext);
    if (context === undefined) {
        throw new Error("useSettings must be used within a SettingsProvider");
    }
    return context;
};
