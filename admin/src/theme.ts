import { createTheme } from "@mui/material/styles";

export const theme = createTheme({
  palette: {
    primary: { main: "#1a365d", light: "#2d5a9e", dark: "#0f2440" },
    secondary: { main: "#28785f", light: "#35a07e", dark: "#1a5a44" },
    warning: { main: "#e8a317" },
    error: { main: "#c53030" },
    success: { main: "#22734b" },
    background: { default: "#f0f4f8", paper: "#ffffff" },
    text: { primary: "#1a202c", secondary: "#64748b" },
  },
  shape: { borderRadius: 12 },
  typography: {
    fontFamily: 'Inter, "Segoe UI", system-ui, sans-serif',
    h3: { fontWeight: 900, letterSpacing: "-0.02em" },
    h4: { fontWeight: 800, letterSpacing: "-0.015em" },
    h5: { fontWeight: 700 },
    h6: { fontWeight: 700 },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: "none",
          fontWeight: 700,
          borderRadius: 10,
          padding: "8px 20px",
        },
        contained: {
          boxShadow: "0 2px 8px rgba(26,54,93,.18)",
          "&:hover": { boxShadow: "0 4px 16px rgba(26,54,93,.24)" },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: "0 1px 3px rgba(0,0,0,.06), 0 8px 30px rgba(26,54,93,.06)",
          border: "1px solid rgba(226,232,240,.6)",
          borderRadius: 16,
        },
      },
    },
    MuiTableContainer: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          border: "1px solid rgba(226,232,240,.6)",
          boxShadow: "0 1px 3px rgba(0,0,0,.04), 0 8px 30px rgba(26,54,93,.05)",
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: { fontWeight: 600, fontSize: "0.75rem" },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        head: {
          fontWeight: 700,
          color: "#64748b",
          fontSize: "0.8rem",
          textTransform: "uppercase",
          letterSpacing: "0.04em",
          borderBottomWidth: 2,
        },
      },
    },
    MuiDialog: {
      styleOverrides: {
        paper: { borderRadius: 20 },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          "& .MuiOutlinedInput-root": {
            borderRadius: 10,
          },
        },
      },
    },
  },
});
