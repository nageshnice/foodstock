import { Add } from "@mui/icons-material";
import { Box, Button, Typography } from "@mui/material";
import type { ReactNode } from "react";

interface Props {
  title: string;
  subtitle: string;
  actionLabel?: string;
  onAction?: () => void;
  action?: ReactNode;
}

export function PageHeader({ title, subtitle, actionLabel, onAction, action }: Props) {
  return (
    <Box
      display="flex"
      justifyContent="space-between"
      alignItems="flex-start"
      mb={2.5}
      gap={2}
      flexWrap="wrap"
    >
      <Box>
        <Typography
          variant="h4"
          fontWeight={800}
          sx={{
            background: "linear-gradient(135deg, #1a365d 0%, #2d5a9e 100%)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
          }}
        >
          {title}
        </Typography>
        <Typography color="text.secondary" sx={{ mt: 0.25 }}>
          {subtitle}
        </Typography>
      </Box>
      {action ??
        (actionLabel && (
          <Button
            variant="contained"
            onClick={onAction}
            startIcon={<Add />}
            sx={{
              px: 3,
              py: 1.2,
              background: "linear-gradient(135deg, #1a365d 0%, #2d5a9e 100%)",
              "&:hover": { background: "linear-gradient(135deg, #0f2440 0%, #1a365d 100%)" },
            }}
          >
            {actionLabel}
          </Button>
        ))}
    </Box>
  );
}
