import {
  CategoryOutlined,
  DashboardOutlined,
  Inventory2Outlined,
  LocalShippingOutlined,
  LogoutOutlined,
  PeopleOutlined,
  ReceiptLongOutlined,
  StorefrontOutlined,
} from "@mui/icons-material";
import {
  AppBar,
  Avatar,
  Box,
  Divider,
  Drawer,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
} from "@mui/material";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { api } from "../api";

const drawerWidth = 260;
const links = [
  ["/", "Dashboard", <DashboardOutlined />],
  ["/products", "Products", <StorefrontOutlined />],
  ["/inventory", "Inventory", <Inventory2Outlined />],
  ["/orders", "Orders", <ReceiptLongOutlined />],
  ["/customers", "Customers", <PeopleOutlined />],
  ["/vendors", "Vendors", <LocalShippingOutlined />],
  ["/catalog", "Regions & Catalog", <CategoryOutlined />],
] as const;

export function AdminLayout() {
  const navigate = useNavigate();
  const logout = async () => {
    try {
      await api.post("/auth/logout");
    } catch {
      /* still clear local session */
    }
    localStorage.removeItem("food_stock_admin_token");
    localStorage.removeItem("food_stock_api_key");
    localStorage.removeItem("food_stock_session_id");
    navigate("/login");
  };
  return (
    <Box display="flex" minHeight="100vh" sx={{ bgcolor: "background.default" }}>
      <AppBar
        position="fixed"
        elevation={0}
        sx={{
          zIndex: (theme) => theme.zIndex.drawer + 1,
          background: "linear-gradient(135deg, #1a365d 0%, #2d5a9e 100%)",
          borderBottom: "1px solid rgba(255,255,255,.08)",
          backdropFilter: "blur(12px)",
        }}
      >
        <Toolbar sx={{ gap: 2 }}>
          <Avatar
            sx={{
              bgcolor: "rgba(255,255,255,.15)",
              width: 36,
              height: 36,
              fontSize: 16,
              fontWeight: 900,
            }}
          >
            FS
          </Avatar>
          <Box>
            <Typography variant="h6" fontWeight={800} sx={{ lineHeight: 1.2 }}>
              Food Stock
            </Typography>
            <Typography
              variant="caption"
              sx={{ color: "rgba(255,255,255,.6)", fontWeight: 600, letterSpacing: "0.08em" }}
            >
              ADMIN OPERATIONS
            </Typography>
          </Box>
        </Toolbar>
      </AppBar>

      <Drawer
        variant="permanent"
        sx={{
          width: drawerWidth,
          "& .MuiDrawer-paper": {
            width: drawerWidth,
            background: "linear-gradient(180deg, #0f2440 0%, #1a365d 100%)",
            borderRight: "none",
            color: "rgba(255,255,255,.85)",
          },
        }}
      >
        <Toolbar />
        <Box px={2.5} pt={3} pb={1}>
          <Typography
            variant="overline"
            sx={{ color: "rgba(255,255,255,.35)", fontWeight: 800, letterSpacing: "0.12em" }}
          >
            Navigation
          </Typography>
        </Box>
        <List sx={{ px: 1.5, flex: 1 }}>
          {links.map(([path, label, icon]) => (
            <ListItemButton
              key={path}
              component={NavLink}
              to={path}
              end={path === "/"}
              sx={{
                borderRadius: 2.5,
                mb: 0.5,
                py: 1.2,
                color: "rgba(255,255,255,.65)",
                "& .MuiListItemIcon-root": { color: "rgba(255,255,255,.45)", minWidth: 40 },
                "&:hover": {
                  bgcolor: "rgba(255,255,255,.06)",
                  color: "rgba(255,255,255,.95)",
                  "& .MuiListItemIcon-root": { color: "rgba(255,255,255,.8)" },
                },
                "&.active": {
                  bgcolor: "rgba(255,255,255,.12)",
                  color: "#ffffff",
                  fontWeight: 700,
                  backdropFilter: "blur(8px)",
                  boxShadow: "0 2px 12px rgba(0,0,0,.15)",
                  "& .MuiListItemIcon-root": { color: "#60a5fa" },
                  "& .MuiListItemText-primary": { fontWeight: 700 },
                },
              }}
            >
              <ListItemIcon>{icon}</ListItemIcon>
              <ListItemText
                primary={label}
                primaryTypographyProps={{ fontSize: "0.9rem", fontWeight: 500 }}
              />
            </ListItemButton>
          ))}
        </List>
        <Divider sx={{ borderColor: "rgba(255,255,255,.08)" }} />
        <ListItemButton
          onClick={logout}
          sx={{
            m: 1.5,
            borderRadius: 2.5,
            color: "rgba(255,255,255,.55)",
            "& .MuiListItemIcon-root": { color: "rgba(255,255,255,.4)", minWidth: 40 },
            "&:hover": {
              bgcolor: "rgba(239,68,68,.12)",
              color: "#fca5a5",
              "& .MuiListItemIcon-root": { color: "#fca5a5" },
            },
          }}
        >
          <ListItemIcon>
            <LogoutOutlined />
          </ListItemIcon>
          <ListItemText primary="Logout" primaryTypographyProps={{ fontWeight: 600 }} />
        </ListItemButton>
      </Drawer>

      <Box
        component="main"
        flex={1}
        p={{ xs: 2, md: 2.5 }}
        mt="64px"
        sx={{ overflowX: "auto", minWidth: 0 }}
      >
        <Outlet />
      </Box>
    </Box>
  );
}
