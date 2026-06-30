import { useState, type FormEvent } from "react";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  InputAdornment,
  TextField,
  Typography,
} from "@mui/material";
import { EmailOutlined, LockOutlined, StorefrontOutlined } from "@mui/icons-material";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api, apiError } from "../api";
import type { ApiResponse } from "../types";

export function LoginPage() {
  const [searchParams] = useSearchParams();
  const sessionExpired = searchParams.get("session") === "expired";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const response = await api.post<
        ApiResponse<{
          access_token: string;
          api_key?: string;
          session_id?: string;
          user: { id: number; email: string; full_name: string | null; role: string };
        }>
      >("/auth/login", { email: email.trim().toLowerCase(), password });
      if (!response.data.data.user.role.includes("admin"))
        throw new Error("This account does not have admin access");
      localStorage.setItem("food_stock_admin_token", response.data.data.access_token);
      localStorage.setItem("food_stock_admin_user", JSON.stringify(response.data.data.user));
      if (response.data.data.api_key) {
        localStorage.setItem("food_stock_api_key", response.data.data.api_key);
      }
      if (response.data.data.session_id) {
        localStorage.setItem("food_stock_session_id", response.data.data.session_id);
      }
      navigate("/");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : apiError(reason));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      minHeight="100vh"
      display="grid"
      sx={{
        placeItems: "center",
        background: "linear-gradient(135deg, #0f2440 0%, #1a365d 40%, #2d5a9e 100%)",
        position: "relative",
        overflow: "hidden",
        "&::before": {
          content: '""',
          position: "absolute",
          top: "-50%",
          right: "-20%",
          width: "600px",
          height: "600px",
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(96,165,250,.12) 0%, transparent 70%)",
        },
        "&::after": {
          content: '""',
          position: "absolute",
          bottom: "-30%",
          left: "-10%",
          width: "500px",
          height: "500px",
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(40,120,95,.1) 0%, transparent 70%)",
        },
      }}
      p={2}
    >
      <Card
        sx={{
          width: "100%",
          maxWidth: 440,
          position: "relative",
          zIndex: 1,
          borderRadius: 5,
          border: "1px solid rgba(255,255,255,.08)",
          boxShadow: "0 25px 60px rgba(0,0,0,.25), 0 0 0 1px rgba(255,255,255,.05) inset",
        }}
      >
        <CardContent sx={{ p: { xs: 4, sm: 5 } }}>
          <Box display="flex" alignItems="center" gap={1.5} mb={1}>
            <Box
              sx={{
                width: 48,
                height: 48,
                borderRadius: 3,
                background: "linear-gradient(135deg, #1a365d 0%, #2d5a9e 100%)",
                display: "grid",
                placeItems: "center",
                boxShadow: "0 4px 12px rgba(26,54,93,.3)",
              }}
            >
              <StorefrontOutlined sx={{ color: "white", fontSize: 26 }} />
            </Box>
            <Box>
              <Typography variant="h5" fontWeight={900} sx={{ lineHeight: 1.1 }}>
                Food Stock
              </Typography>
              <Typography
                variant="caption"
                color="primary"
                fontWeight={800}
                sx={{ letterSpacing: "0.08em" }}
              >
                ADMIN PORTAL
              </Typography>
            </Box>
          </Box>
          <Typography color="text.secondary" mb={4} sx={{ fontSize: "0.9rem" }}>
            Manage imported pantry products, stock, vendors and orders.
          </Typography>

          {sessionExpired && !error && (
            <Alert severity="info" sx={{ mb: 3, borderRadius: 3 }}>
              Your session has expired. Please sign in again to continue.
            </Alert>
          )}

          {error && (
            <Alert
              severity="error"
              sx={{ mb: 2.5, borderRadius: 2.5 }}
              onClose={() => setError("")}
            >
              {error}
            </Alert>
          )}

          <Box component="form" onSubmit={submit} display="grid" gap={2.5}>
            <TextField
              id="login-email"
              label="Admin email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              slotProps={{
                input: {
                  startAdornment: (
                    <InputAdornment position="start">
                      <EmailOutlined sx={{ color: "text.secondary" }} />
                    </InputAdornment>
                  ),
                },
              }}
            />
            <TextField
              id="login-password"
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              slotProps={{
                input: {
                  startAdornment: (
                    <InputAdornment position="start">
                      <LockOutlined sx={{ color: "text.secondary" }} />
                    </InputAdornment>
                  ),
                },
              }}
            />
            <Button
              id="login-submit"
              type="submit"
              variant="contained"
              size="large"
              disabled={loading}
              sx={{
                py: 1.5,
                mt: 1,
                fontSize: "1rem",
                background: "linear-gradient(135deg, #1a365d 0%, #2d5a9e 100%)",
                "&:hover": { background: "linear-gradient(135deg, #0f2440 0%, #1a365d 100%)" },
              }}
            >
              {loading ? <CircularProgress size={24} color="inherit" /> : "Sign in to Dashboard"}
            </Button>
          </Box>

          <Typography
            variant="caption"
            color="text.secondary"
            display="block"
            textAlign="center"
            mt={3}
          >
            Faridi Impex Pvt. Ltd. — Imported Pantry Operations
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
}
