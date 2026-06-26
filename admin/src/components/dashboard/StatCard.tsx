import { Box, Card, CardContent, Typography } from "@mui/material";
import type { ReactNode } from "react";

interface Props {
  label: string;
  value: string | number;
  hint?: string;
  icon: ReactNode;
  gradient: string;
  accent: string;
}

export function StatCard({ label, value, hint, icon, gradient, accent }: Props) {
  return (
    <Card
      sx={{
        height: "100%",
        background: gradient,
        border: "none",
        color: "#fff",
        position: "relative",
        overflow: "hidden",
        "&::after": {
          content: '""',
          position: "absolute",
          width: 140,
          height: 140,
          borderRadius: "50%",
          bgcolor: "rgba(255,255,255,.08)",
          top: -40,
          right: -30,
        },
      }}
    >
      <CardContent sx={{ p: 2.5, "&:last-child": { pb: 2.5 }, position: "relative", zIndex: 1 }}>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" gap={2}>
          <Box>
            <Typography
              variant="caption"
              sx={{ color: "rgba(255,255,255,.82)", fontWeight: 700, letterSpacing: "0.06em" }}
            >
              {label}
            </Typography>
            <Typography variant="h4" fontWeight={900} mt={0.75} sx={{ lineHeight: 1.1 }}>
              {value}
            </Typography>
            {hint && (
              <Typography variant="caption" sx={{ color: "rgba(255,255,255,.7)", mt: 1, display: "block" }}>
                {hint}
              </Typography>
            )}
          </Box>
          <Box
            sx={{
              width: 48,
              height: 48,
              borderRadius: 2.5,
              bgcolor: accent,
              display: "grid",
              placeItems: "center",
              flexShrink: 0,
              boxShadow: "0 8px 20px rgba(0,0,0,.12)",
            }}
          >
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}
