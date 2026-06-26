import { useCallback, useEffect, useState, type MouseEvent } from "react";
import {
  Avatar,
  Badge,
  Box,
  Chip,
  Divider,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  Popover,
  Tooltip,
  Typography,
} from "@mui/material";
import {
  AccountCircleOutlined,
  DashboardOutlined,
  LogoutOutlined,
  NotificationsNoneOutlined,
  ReceiptLongOutlined,
  SettingsOutlined,
  WarningAmberOutlined,
} from "@mui/icons-material";
import { useNavigate } from "react-router-dom";
import { api, apiError } from "../api";
import type { AdminAlert, AdminProfile, ApiResponse } from "../types";

const ADMIN_USER_KEY = "food_stock_admin_user";

const SEVERITY_COLOR: Record<string, string> = {
  warning: "#e8a317",
  info: "#2d5a9e",
  success: "#22734b",
  error: "#c53030",
};

function readCachedProfile(): AdminProfile | null {
  try {
    const raw = localStorage.getItem(ADMIN_USER_KEY);
    return raw ? (JSON.parse(raw) as AdminProfile) : null;
  } catch {
    return null;
  }
}

function initials(profile: AdminProfile | null) {
  if (profile?.full_name?.trim()) {
    return profile.full_name
      .split(" ")
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase() ?? "")
      .join("");
  }
  return profile?.email?.[0]?.toUpperCase() ?? "A";
}

interface Props {
  onLogout: () => void;
}

export function AdminHeader({ onLogout }: Props) {
  const navigate = useNavigate();
  const [profile, setProfile] = useState<AdminProfile | null>(readCachedProfile);
  const [alerts, setAlerts] = useState<AdminAlert[]>([]);
  const [alertAnchor, setAlertAnchor] = useState<HTMLElement | null>(null);
  const [profileAnchor, setProfileAnchor] = useState<HTMLElement | null>(null);
  const [readIds, setReadIds] = useState<Set<string>>(() => new Set());

  const loadHeaderData = useCallback(async () => {
    try {
      const [profileRes, alertsRes] = await Promise.all([
        api.get<ApiResponse<AdminProfile>>("/admin/me"),
        api.get<ApiResponse<AdminAlert[]>>("/admin/alerts"),
      ]);
      setProfile(profileRes.data.data);
      localStorage.setItem(ADMIN_USER_KEY, JSON.stringify(profileRes.data.data));
      setAlerts(alertsRes.data.data);
    } catch (e) {
      console.warn(apiError(e));
    }
  }, []);

  useEffect(() => {
    loadHeaderData();
    const timer = window.setInterval(loadHeaderData, 60000);
    return () => window.clearInterval(timer);
  }, [loadHeaderData]);

  const unreadCount = alerts.filter((alert) => !readIds.has(alert.id)).length;

  const openAlerts = (event: MouseEvent<HTMLElement>) => {
    setAlertAnchor(event.currentTarget);
    setReadIds(new Set(alerts.map((alert) => alert.id)));
  };

  const roleLabel = profile?.role?.replace("_", " ") ?? "admin";

  return (
    <Box display="flex" alignItems="center" gap={1} ml="auto">
      <Tooltip title="Alerts & notifications">
        <IconButton
          onClick={openAlerts}
          sx={{
            color: "rgba(255,255,255,.9)",
            bgcolor: "rgba(255,255,255,.08)",
            "&:hover": { bgcolor: "rgba(255,255,255,.14)" },
          }}
        >
          <Badge badgeContent={unreadCount} color="error" max={9}>
            <NotificationsNoneOutlined />
          </Badge>
        </IconButton>
      </Tooltip>

      <Popover
        open={Boolean(alertAnchor)}
        anchorEl={alertAnchor}
        onClose={() => setAlertAnchor(null)}
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
        transformOrigin={{ vertical: "top", horizontal: "right" }}
        slotProps={{
          paper: {
            sx: {
              width: 360,
              mt: 1,
              borderRadius: 3,
              boxShadow: "0 16px 48px rgba(15,36,64,.18)",
            },
          },
        }}
      >
        <Box px={2} py={1.5}>
          <Typography variant="subtitle1" fontWeight={800}>
            Admin Alerts
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Store operations requiring your attention
          </Typography>
        </Box>
        <Divider />
        {alerts.length === 0 ? (
          <Box px={2} py={4} textAlign="center" color="text.secondary">
            <NotificationsNoneOutlined sx={{ fontSize: 36, opacity: 0.35, mb: 1 }} />
            <Typography variant="body2">All clear — no alerts right now</Typography>
          </Box>
        ) : (
          <List dense disablePadding>
            {alerts.map((alert) => (
              <ListItemButton
                key={alert.id}
                onClick={() => {
                  setAlertAnchor(null);
                  if (alert.href) navigate(alert.href);
                }}
                sx={{ py: 1.25, alignItems: "flex-start" }}
              >
                <ListItemIcon sx={{ minWidth: 36, mt: 0.25 }}>
                  <WarningAmberOutlined
                    sx={{ color: SEVERITY_COLOR[alert.severity] ?? "#64748b" }}
                  />
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Typography variant="body2" fontWeight={700}>
                      {alert.title}
                    </Typography>
                  }
                  secondary={alert.message}
                />
              </ListItemButton>
            ))}
          </List>
        )}
      </Popover>

      <Tooltip title="Account menu">
        <IconButton
          onClick={(e) => setProfileAnchor(e.currentTarget)}
          sx={{ p: 0.5, ml: 0.5 }}
        >
          <Avatar
            src={profile?.image_url ?? undefined}
            sx={{
              width: 38,
              height: 38,
              bgcolor: "rgba(255,255,255,.18)",
              border: "2px solid rgba(255,255,255,.35)",
              fontWeight: 800,
              fontSize: "0.9rem",
            }}
          >
            {initials(profile)}
          </Avatar>
        </IconButton>
      </Tooltip>

      <Menu
        anchorEl={profileAnchor}
        open={Boolean(profileAnchor)}
        onClose={() => setProfileAnchor(null)}
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
        transformOrigin={{ vertical: "top", horizontal: "right" }}
        slotProps={{
          paper: {
            sx: {
              width: 280,
              mt: 1.5,
              borderRadius: 3,
              boxShadow: "0 16px 48px rgba(15,36,64,.18)",
            },
          },
        }}
      >
        <Box px={2} py={1.5}>
          <Typography variant="subtitle1" fontWeight={800} noWrap>
            {profile?.full_name ?? "Admin User"}
          </Typography>
          <Typography variant="body2" color="text.secondary" noWrap>
            {profile?.email ?? "—"}
          </Typography>
          <Chip
            label={roleLabel}
            size="small"
            sx={{
              mt: 1,
              textTransform: "capitalize",
              fontWeight: 700,
              bgcolor: "rgba(26,54,93,.08)",
              color: "#1a365d",
            }}
          />
        </Box>
        <Divider />
        <MenuItem
          onClick={() => {
            setProfileAnchor(null);
            navigate("/");
          }}
        >
          <ListItemIcon>
            <DashboardOutlined fontSize="small" />
          </ListItemIcon>
          Dashboard
        </MenuItem>
        <MenuItem
          onClick={() => {
            setProfileAnchor(null);
            navigate("/orders");
          }}
        >
          <ListItemIcon>
            <ReceiptLongOutlined fontSize="small" />
          </ListItemIcon>
          Orders
        </MenuItem>
        <MenuItem disabled>
          <ListItemIcon>
            <SettingsOutlined fontSize="small" />
          </ListItemIcon>
          Settings
        </MenuItem>
        <MenuItem disabled>
          <ListItemIcon>
            <AccountCircleOutlined fontSize="small" />
          </ListItemIcon>
          My Profile
        </MenuItem>
        <Divider />
        <MenuItem
          onClick={() => {
            setProfileAnchor(null);
            onLogout();
          }}
          sx={{ color: "error.main" }}
        >
          <ListItemIcon>
            <LogoutOutlined fontSize="small" color="error" />
          </ListItemIcon>
          Sign out
        </MenuItem>
      </Menu>
    </Box>
  );
}
