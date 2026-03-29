"use client";

import { useEffect, useRef, useState } from "react";
import type { CSSProperties } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { useAuth } from "@/components/auth-provider";
import { api } from "@/lib/api";
import { openPaddleCheckout } from "@/lib/paddle";
import {
  ShieldCheck, Plug, FileText, Zap, ArrowRight, CheckCircle2,
  BarChart3, Lock, Star, Clock, TrendingUp, TrendingDown, Users, ChevronDown,
  Menu, X, AlertTriangle, BookOpen, GraduationCap, Target,
  Globe, ClipboardList, Building2, UserCheck, Shield,
  Siren, Server, Bug, RefreshCw, Database, Workflow,
  Sparkles, ClipboardCheck, Network, Github, Twitter, Linkedin,
} from "lucide-react";

// ── Integration logos ────────────────────────────────────────────────────────

function AwsLogo() {
  return (
    <svg width="48" height="30" viewBox="0 0 48 30" fill="none">
      <text x="0" y="21" fontSize="20" fontWeight="900" fill="#FF9900" fontFamily="Arial,sans-serif">aws</text>
      <path d="M2 26 Q24 32 46 26" stroke="#FF9900" strokeWidth="2" fill="none" strokeLinecap="round"/>
    </svg>
  );
}

function GithubLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="#1f2937">
      <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/>
    </svg>
  );
}

function SlackLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <path d="M5.042 15.165a2.528 2.528 0 01-2.52 2.523A2.528 2.528 0 010 15.165a2.527 2.527 0 012.522-2.52h2.52v2.52zM6.313 15.165a2.527 2.527 0 012.521-2.52 2.527 2.527 0 012.521 2.52v6.313A2.528 2.528 0 018.834 24a2.528 2.528 0 01-2.521-2.522v-6.313z" fill="#E01E5A"/>
      <path d="M8.834 5.042a2.528 2.528 0 01-2.521-2.52A2.528 2.528 0 018.834 0a2.528 2.528 0 012.521 2.522v2.52H8.834zM8.834 6.313a2.528 2.528 0 012.521 2.521 2.528 2.528 0 01-2.521 2.521H2.522A2.528 2.528 0 010 8.834a2.528 2.528 0 012.522-2.521h6.312z" fill="#36C5F0"/>
      <path d="M18.956 8.834a2.528 2.528 0 012.522-2.521A2.528 2.528 0 0124 8.834a2.528 2.528 0 01-2.522 2.521h-2.522V8.834zM17.688 8.834a2.528 2.528 0 01-2.523 2.521 2.527 2.527 0 01-2.52-2.521V2.522A2.527 2.527 0 0115.165 0a2.528 2.528 0 012.523 2.522v6.312z" fill="#2EB67D"/>
      <path d="M15.165 18.956a2.528 2.528 0 012.523 2.522A2.528 2.528 0 0115.165 24a2.527 2.527 0 01-2.52-2.522v-2.522h2.52zM15.165 17.688a2.527 2.527 0 01-2.52-2.523 2.526 2.526 0 012.52-2.52h6.313A2.527 2.527 0 0124 15.165a2.528 2.528 0 01-2.522 2.523h-6.313z" fill="#ECB22E"/>
    </svg>
  );
}

function GoogleLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
    </svg>
  );
}

function JiraLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <defs>
        <linearGradient id="jira-g1" x1="16.2" y1="6.11" x2="10.6" y2="0.89" gradientUnits="userSpaceOnUse">
          <stop stopColor="#0052CC"/><stop offset="1" stopColor="#2684FF"/>
        </linearGradient>
        <linearGradient id="jira-g2" x1="7.5" y1="11.57" x2="13.9" y2="18.3" gradientUnits="userSpaceOnUse">
          <stop stopColor="#0052CC"/><stop offset="1" stopColor="#2684FF"/>
        </linearGradient>
      </defs>
      <path d="M11.571 11.513H0a5.218 5.218 0 005.232 5.215h2.13v2.057A5.215 5.215 0 0012.575 24V12.518a1.005 1.005 0 00-1.004-1.005z" fill="#2684FF"/>
      <path d="M6.107 6.108H17.678A5.218 5.218 0 0012.446.893h-2.13V-1.16A5.215 5.215 0 005.103 4.054v2.049h1.004z" fill="url(#jira-g1)"/>
      <path d="M17.679 6.107H6.108a5.218 5.218 0 005.232 5.215h2.13v2.057A5.215 5.215 0 0018.683 18.6V7.112a1.005 1.005 0 00-1.004-1.005z" fill="url(#jira-g2)"/>
    </svg>
  );
}

function OktaLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="12" r="11" fill="#007DC1"/>
      <circle cx="12" cy="12" r="4.5" fill="white"/>
    </svg>
  );
}

function AzureLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <path d="M13.05 4.24L6.56 19.03l14.96.01L13.05 4.24z" fill="#0078D4"/>
      <path d="M13.29 4.24L8.73 10.9l4.44 8.13H2.48L13.29 4.24z" fill="#0078D4" opacity=".7"/>
    </svg>
  );
}

function GitLabLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <path d="M23.955 13.587l-1.342-4.135-2.664-8.189a.455.455 0 00-.867 0L16.418 9.45H7.582L4.918 1.263a.455.455 0 00-.867 0L1.386 9.45.044 13.587a.924.924 0 00.331 1.023L12 23.054l11.625-8.443a.92.92 0 00.33-1.024" fill="#FC6D26"/>
      <path d="M12 23.054l4.418-13.605H7.582z" fill="#E24329"/>
      <path d="M12 23.054L7.582 9.449H1.386z" fill="#FC6D26"/>
      <path d="M1.386 9.45L.044 13.587a.924.924 0 00.331 1.023L12 23.054z" fill="#FCA326"/>
      <path d="M1.386 9.45h6.196L4.918 1.263a.456.456 0 00-.867 0z" fill="#E24329"/>
      <path d="M12 23.054l4.418-13.605h6.196z" fill="#FC6D26"/>
      <path d="M22.614 9.45l1.341 4.137a.924.924 0 01-.331 1.023L12 23.054z" fill="#FCA326"/>
      <path d="M22.614 9.45h-6.196l2.664-8.187a.455.455 0 01.867 0z" fill="#E24329"/>
    </svg>
  );
}

function GCPLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <path d="M12 6.5L14.5 4H9.5L12 6.5z" fill="#EA4335"/>
      <path d="M18 8.5l2.5-2.5h-5L18 8.5z" fill="#4285F4"/>
      <path d="M6 8.5l2.5-2.5h-5L6 8.5z" fill="#FBBC05"/>
      <rect x="4" y="9" width="16" height="8" rx="4" fill="#34A853"/>
      <circle cx="8" cy="13" r="1.5" fill="white"/>
      <circle cx="12" cy="13" r="1.5" fill="white"/>
      <circle cx="16" cy="13" r="1.5" fill="white"/>
    </svg>
  );
}

function LinearLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <defs>
        <linearGradient id="linear-g" x1="0" y1="0" x2="24" y2="24" gradientUnits="userSpaceOnUse">
          <stop stopColor="#5E6AD2"/><stop offset="1" stopColor="#8B8FF0"/>
        </linearGradient>
      </defs>
      <path d="M3.5 17.5L17.5 3.5M3.5 17.5l3.5 3.5M3.5 17.5l-3.5-3.5M17.5 3.5l3.5 3.5M17.5 3.5l-3.5-3.5" stroke="url(#linear-g)" strokeWidth="2" strokeLinecap="round"/>
      <circle cx="12" cy="12" r="5" stroke="url(#linear-g)" strokeWidth="2"/>
    </svg>
  );
}

function DatadogLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <rect width="24" height="24" rx="6" fill="#632CA6"/>
      <path d="M7 8h10M7 12h7M7 16h10" stroke="white" strokeWidth="1.8" strokeLinecap="round"/>
      <circle cx="17" cy="12" r="2" fill="#7241D0"/>
      <circle cx="17" cy="12" r="1" fill="white"/>
    </svg>
  );
}

function PagerDutyLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <rect width="24" height="24" rx="6" fill="#06AC38"/>
      <rect x="10" y="5" width="4" height="10" rx="2" fill="white"/>
      <circle cx="12" cy="18" r="2" fill="white"/>
    </svg>
  );
}

function SentryLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <path d="M13.414 2.586a2 2 0 00-2.828 0L2.586 11.586a2 2 0 000 2.828l3.536 3.536h11.314l3.536-3.536a2 2 0 000-2.828L13.414 2.586z" fill="#362D59"/>
      <path d="M12 8v5M12 15v1" stroke="white" strokeWidth="2" strokeLinecap="round"/>
    </svg>
  );
}

function TeamsLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <rect width="24" height="24" rx="6" fill="#5059C9"/>
      <circle cx="15" cy="8" r="3" fill="#7B83EB"/>
      <rect x="9" y="11" width="12" height="8" rx="2" fill="#5059C9"/>
      <circle cx="9" cy="9" r="2.5" fill="#7B83EB"/>
      <rect x="3" y="12" width="10" height="7" rx="2" fill="#7B83EB"/>
    </svg>
  );
}

function StripeLogo() {
  return (
    <svg width="36" height="18" viewBox="0 0 60 25" fill="none">
      <text x="0" y="20" fontSize="20" fontWeight="700" fill="#635BFF" fontFamily="Arial,sans-serif">stripe</text>
    </svg>
  );
}

function RipplingLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <rect width="24" height="24" rx="6" fill="#F36C21"/>
      <path d="M7 12a5 5 0 005 5V7a5 5 0 00-5 5z" fill="white"/>
      <path d="M12 7a5 5 0 015 5 5 5 0 01-5 5" stroke="white" strokeWidth="1.5" fill="none"/>
    </svg>
  );
}

function BambooLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <rect width="24" height="24" rx="6" fill="#73AC39"/>
      <path d="M9 20V8M9 8C9 5.8 10.8 4 13 4s4 1.8 4 4-1.8 4-4 4H9" stroke="white" strokeWidth="1.8" strokeLinecap="round"/>
      <path d="M9 13c0 2.2-1.8 4-4 4" stroke="white" strokeWidth="1.8" strokeLinecap="round"/>
    </svg>
  );
}

function NotionLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <rect width="24" height="24" rx="4" fill="#191919"/>
      <path d="M6 5.5h8l4 4.5V19a.5.5 0 01-.5.5H6a.5.5 0 01-.5-.5V6a.5.5 0 01.5-.5z" fill="white"/>
      <path d="M14 5.5V10H18" stroke="#191919" strokeWidth="1"/>
      <path d="M9 13h6M9 16h4" stroke="#9B9B9B" strokeWidth="1.3" strokeLinecap="round"/>
    </svg>
  );
}

function CloudflareLogo() {
  return (
    <svg width="34" height="26" viewBox="0 0 54 24" fill="none">
      <path d="M33.5 15.5c.2-.6.1-1.3-.2-1.8-.3-.5-.9-.8-1.5-.9l-16.3-.2c-.1 0-.2-.1-.3-.1-.1-.1-.1-.2 0-.3l.3-.8c.2-.6.1-1.3-.2-1.8-.3-.5-.9-.8-1.5-.9L8 9.5c-2.1 0-3.9 1.3-4.6 3.2l-.9 2.5c-.1.3.1.6.4.6l29.2.2c.3 0 .6-.2.7-.5l.7-2z" fill="#F6821F"/>
      <path d="M37.8 10.3c-.1 0-.3 0-.4.1l-.4 1.1c-.2.6-.1 1.3.2 1.8.3.5.9.8 1.5.9l2.1.1c.1 0 .2.1.3.1.1.1.1.2 0 .3l-.3.8c-.2.6-.1 1.3.2 1.8.3.5.9.8 1.5.9h1.8c2.1 0 3.9-1.3 4.6-3.2l.3-.9c.1-.3-.1-.6-.4-.6l-11-.2z" fill="#FBAD41"/>
      <path d="M20 8.5c-.2 0-.4.1-.5.3l-.5 1.4c-.3.8-.1 1.7.4 2.4.5.6 1.2 1 2 1l21.8.2c.2 0 .3-.1.4-.3.1-.1 0-.3-.1-.4-.8-1.5-2.4-2.5-4.1-2.5l-1.5-.1c-.2 0-.4-.1-.5-.3-.1-.2-.1-.4 0-.5.5-1.5-.5-3.2-2.1-3.5-.2 0-.3 0-.5.1-.6-2.8-3.1-4.8-6-4.8-3.2 0-5.9 2.4-6.3 5.6-.3-.1-.5-.1-.8-.1z" fill="#F6821F"/>
    </svg>
  );
}

function JamfLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <rect width="24" height="24" rx="6" fill="#0079C8"/>
      <text x="3" y="17" fontSize="11" fontWeight="900" fill="white" fontFamily="Arial,sans-serif">jamf</text>
    </svg>
  );
}

function OnePasswordLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <rect width="24" height="24" rx="6" fill="#0C5C99"/>
      <circle cx="12" cy="12" r="6" fill="none" stroke="white" strokeWidth="1.5"/>
      <circle cx="12" cy="12" r="2.5" fill="white"/>
      <path d="M12 6V4M12 20v-2M6 12H4M20 12h-2" stroke="white" strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  );
}

function CrowdStrikeLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <rect width="24" height="24" rx="6" fill="#E31837"/>
      <path d="M6 12l4-4 4 4-4 4-4-4zM14 12l4-4" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

function VercelLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <path d="M12 2L22 20H2L12 2z" fill="#000000"/>
    </svg>
  );
}

function TerraformLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <path d="M9 4.5v6l5.5 3.2V7.7L9 4.5z" fill="#7B42BC"/>
      <path d="M15.5 7.7v6l5.5-3.2V4.5l-5.5 3.2z" fill="#5C35A3"/>
      <path d="M3 7.7v6l5.5 3.2v-6L3 7.7z" fill="#9C6ADE"/>
      <path d="M9 16.3v-2.1l-5.5-3.2v2.1L9 16.3z" fill="#7B42BC" opacity=".5"/>
    </svg>
  );
}

function DuoLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <rect width="24" height="24" rx="6" fill="#6DBE45"/>
      <text x="3" y="17" fontSize="11" fontWeight="900" fill="white" fontFamily="Arial,sans-serif">duo</text>
    </svg>
  );
}

function WizLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <rect width="24" height="24" rx="6" fill="#00BFA5"/>
      <path d="M8 17l2.5-5.5L13 14l2-7 3 10H6l2-10" stroke="white" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
    </svg>
  );
}

function SnykLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <rect width="24" height="24" rx="6" fill="#4C4A73"/>
      <path d="M7 7l5 5-5 5M12 12h5" stroke="#00C4B4" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

function SentinelOneLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <rect width="24" height="24" rx="6" fill="#7E2FD8"/>
      <path d="M12 4L6 8v5c0 3 2.5 5.5 6 7 3.5-1.5 6-4 6-7V8l-6-4z" fill="none" stroke="white" strokeWidth="1.5"/>
      <path d="M9 12l2 2 4-4" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

function HackerOneLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <rect width="24" height="24" rx="6" fill="#272727"/>
      <text x="4" y="16" fontSize="10" fontWeight="900" fill="#FE6A37" fontFamily="Arial,sans-serif">H1</text>
    </svg>
  );
}

function KandjiLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <rect width="24" height="24" rx="6" fill="#1B1B2A"/>
      <path d="M8 6v12M8 12l5-6M8 12l5 6" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

function KolideLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <rect width="24" height="24" rx="6" fill="#00A878"/>
      <circle cx="12" cy="12" r="5" stroke="white" strokeWidth="1.8" fill="none"/>
      <circle cx="12" cy="12" r="2" fill="white"/>
    </svg>
  );
}

function SplunkLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <rect width="24" height="24" rx="6" fill="#65A637"/>
      <path d="M6 16l4-8 2 5 2-3 2 4" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
    </svg>
  );
}

function ConfluenceLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <rect width="24" height="24" rx="6" fill="#0052CC"/>
      <path d="M4.5 17.5c3-4 5-6.5 7.5-6.5s4.5 2.5 7.5 6.5" stroke="white" strokeWidth="1.8" strokeLinecap="round" fill="none"/>
      <path d="M4.5 6.5c3 4 5 6.5 7.5 6.5s4.5-2.5 7.5-6.5" stroke="#7AB3F5" strokeWidth="1.8" strokeLinecap="round" fill="none"/>
    </svg>
  );
}

function ServiceNowLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <rect width="24" height="24" rx="6" fill="#81B5A1"/>
      <path d="M7 12a5 5 0 0110 0 5 5 0 01-10 0z" fill="white"/>
      <path d="M12 9v6M9 12h6" stroke="#81B5A1" strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  );
}
function JumpCloudLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <rect width="24" height="24" rx="6" fill="#0073E6"/>
      <text x="3.5" y="16" fontSize="9" fontWeight="900" fill="white" fontFamily="Arial,sans-serif">JC</text>
    </svg>
  );
}
function BitbucketLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <rect width="24" height="24" rx="6" fill="#0052CC"/>
      <path d="M4 7l3.5 10 5-6 5 6L21 7z" fill="white" opacity="0.9"/>
      <path d="M12.5 11l-1 6h1l1-6z" fill="#0052CC"/>
    </svg>
  );
}
function ZendeskLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <rect width="24" height="24" rx="6" fill="#03363D"/>
      <path d="M7 8a5 5 0 0110 0v1H7V8z" fill="#00363D"/>
      <path d="M7 9h10l-2 7H9L7 9z" fill="white"/>
    </svg>
  );
}
function KubernetesLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <rect width="24" height="24" rx="6" fill="#326CE5"/>
      <circle cx="12" cy="12" r="5" stroke="white" strokeWidth="1.5" fill="none"/>
      <line x1="12" y1="7" x2="12" y2="17" stroke="white" strokeWidth="1.2"/>
      <line x1="7" y1="12" x2="17" y2="12" stroke="white" strokeWidth="1.2"/>
      <line x1="8.5" y1="8.5" x2="15.5" y2="15.5" stroke="white" strokeWidth="1.2"/>
      <line x1="15.5" y1="8.5" x2="8.5" y2="15.5" stroke="white" strokeWidth="1.2"/>
    </svg>
  );
}
function CircleCILogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <rect width="24" height="24" rx="6" fill="#343434"/>
      <circle cx="12" cy="12" r="5" stroke="#F5A623" strokeWidth="1.8" fill="none"/>
      <circle cx="12" cy="12" r="2" fill="#F5A623"/>
    </svg>
  );
}
function QualysLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <rect width="24" height="24" rx="6" fill="#E2002A"/>
      <text x="3" y="16" fontSize="9" fontWeight="900" fill="white" fontFamily="Arial,sans-serif">QL</text>
    </svg>
  );
}

function SegmentLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <rect width="24" height="24" rx="6" fill="#52BD95"/>
      <path d="M7 12h10M7 8h5M7 16h8" stroke="white" strokeWidth="1.8" strokeLinecap="round"/>
    </svg>
  );
}

function HubSpotLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <rect width="24" height="24" rx="6" fill="#FF7A59"/>
      <circle cx="14.5" cy="9.5" r="3" fill="white"/>
      <circle cx="9.5" cy="14.5" r="2" fill="white"/>
      <path d="M11.5 9.5H7M14.5 12.5v5" stroke="white" strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  );
}

function SalesforceLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <rect width="24" height="24" rx="6" fill="#00A1E0"/>
      <path d="M12 5c-2.2 0-4 1.6-4 3.6 0 .4.1.8.2 1.1-1 .3-1.7 1.2-1.7 2.3 0 1.4 1.1 2.5 2.5 2.5h6c1.4 0 2.5-1.1 2.5-2.5 0-1-.6-1.9-1.5-2.3C16 8.2 14.2 5 12 5z" fill="white"/>
    </svg>
  );
}

function MailchimpLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <rect width="24" height="24" rx="6" fill="#FFE01B"/>
      <path d="M12 5c-2 0-4 1.5-4 4 0 .8.2 1.5.6 2.1C7.6 11.6 7 12.5 7 13.5c0 1.7 2.2 3 5 3s5-1.3 5-3c0-1-.6-1.9-1.6-2.4.4-.6.6-1.3.6-2.1C16 6.5 14 5 12 5z" fill="#241C15"/>
    </svg>
  );
}

function OpenAILogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <rect width="24" height="24" rx="6" fill="#000000"/>
      <path d="M12 4.5a7.5 7.5 0 100 15 7.5 7.5 0 000-15zm0 2a5.5 5.5 0 110 11 5.5 5.5 0 010-11z" fill="white" opacity="0.9"/>
      <path d="M12 7.5a4.5 4.5 0 100 9 4.5 4.5 0 000-9z" fill="white" opacity="0.5"/>
      <circle cx="12" cy="12" r="2" fill="white"/>
    </svg>
  );
}

function AnthropicLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <rect width="24" height="24" rx="6" fill="#CC785C"/>
      <path d="M8.5 17l3.5-10 3.5 10M10 13.5h5" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

function HarvestLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <rect width="24" height="24" rx="6" fill="#FA5D00"/>
      <circle cx="12" cy="12" r="5" stroke="white" strokeWidth="1.8" fill="none"/>
      <path d="M12 7v5l3 3" stroke="white" strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  );
}

function LeverLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <rect width="24" height="24" rx="6" fill="#1A1A2E"/>
      <text x="4" y="16" fontSize="10" fontWeight="900" fill="white" fontFamily="Arial,sans-serif">LVR</text>
    </svg>
  );
}

const INTEGRATION_LOGOS = [
  { name: "AWS",              logo: <AwsLogo />       },
  { name: "GitHub",           logo: <GithubLogo />    },
  { name: "Slack",            logo: <SlackLogo />     },
  { name: "Google Workspace", logo: <GoogleLogo />    },
  { name: "Okta",             logo: <OktaLogo />      },
  { name: "Azure AD",         logo: <AzureLogo />     },
  { name: "Jira",             logo: <JiraLogo />      },
  { name: "GitLab",           logo: <GitLabLogo />    },
  { name: "GCP",              logo: <GCPLogo />       },
  { name: "Linear",           logo: <LinearLogo />    },
  { name: "Datadog",          logo: <DatadogLogo />   },
  { name: "PagerDuty",        logo: <PagerDutyLogo /> },
  { name: "Sentry",           logo: <SentryLogo />    },
  { name: "Teams",            logo: <TeamsLogo />     },
  { name: "Stripe",           logo: <StripeLogo />        },
  { name: "Rippling",         logo: <RipplingLogo />      },
  { name: "BambooHR",         logo: <BambooLogo />        },
  { name: "Notion",           logo: <NotionLogo />        },
  { name: "Cloudflare",       logo: <CloudflareLogo />    },
  { name: "Jamf",             logo: <JamfLogo />          },
  { name: "1Password",        logo: <OnePasswordLogo />   },
  { name: "CrowdStrike",      logo: <CrowdStrikeLogo />   },
  { name: "Vercel",           logo: <VercelLogo />        },
  { name: "Terraform",        logo: <TerraformLogo />     },
  { name: "Duo Security",     logo: <DuoLogo />           },
  { name: "Wiz",              logo: <WizLogo />           },
  { name: "Snyk",             logo: <SnykLogo />          },
  { name: "SentinelOne",      logo: <SentinelOneLogo />   },
  { name: "HackerOne",        logo: <HackerOneLogo />     },
  { name: "Kandji",           logo: <KandjiLogo />        },
  { name: "Kolide",           logo: <KolideLogo />        },
  { name: "Splunk",           logo: <SplunkLogo />        },
  { name: "Confluence",       logo: <ConfluenceLogo />    },
  { name: "ServiceNow",       logo: <ServiceNowLogo />    },
  { name: "JumpCloud",        logo: <JumpCloudLogo />     },
  { name: "Bitbucket",        logo: <BitbucketLogo />     },
  { name: "Zendesk",          logo: <ZendeskLogo />       },
  { name: "Kubernetes",       logo: <KubernetesLogo />    },
  { name: "CircleCI",         logo: <CircleCILogo />      },
  { name: "Qualys",           logo: <QualysLogo />        },
  { name: "Segment",          logo: <SegmentLogo />       },
  { name: "HubSpot",          logo: <HubSpotLogo />       },
  { name: "Salesforce",       logo: <SalesforceLogo />    },
  { name: "Mailchimp",        logo: <MailchimpLogo />     },
  { name: "OpenAI",           logo: <OpenAILogo />        },
  { name: "Anthropic",        logo: <AnthropicLogo />     },
  { name: "Harvest",          logo: <HarvestLogo />       },
  { name: "Lever",            logo: <LeverLogo />         },
];

// ── Static data ───────────────────────────────────────────────────────────────

const STATS = [
  { value: "120+", label: "integrations, ready to connect" },
  { value: "9",    label: "frameworks, one platform"       },
  { value: "3",    label: "AI engines, always running"     },
  { value: "24h",  label: "evidence collection cycle"      },
];

const FRAMEWORKS = [
  { name: "SOC 2",    desc: "Type I & II — toggle in readiness view",       detail: "Trust Service Criteria — security, availability, confidentiality, and privacy", color: "from-teal-500 to-emerald-500" },
  { name: "ISO 27001",desc: "2022 Edition",      detail: "93 Annex A controls across 4 themes — organizational, people, physical, technological", color: "from-blue-500 to-cyan-500" },
  { name: "HIPAA",    desc: "Security Rule",     detail: "Administrative, physical, and technical safeguards for protected health information", color: "from-violet-500 to-purple-500" },
  { name: "GDPR",     desc: "EU Regulation",     detail: "Data protection by design, DPIA, consent management, DPO, and breach notification", color: "from-indigo-500 to-blue-500" },
  { name: "PCI DSS",  desc: "v4.0",              detail: "12 requirements for organizations that process, store, or transmit cardholder data", color: "from-amber-500 to-orange-500" },
  { name: "CCPA",     desc: "California Privacy", detail: "Consumer rights, data inventory, opt-out mechanisms, and service provider controls", color: "from-rose-500 to-pink-500" },
  { name: "NIST CSF", desc: "Framework 2.0",     detail: "Identify, protect, detect, respond, and recover — the cybersecurity lifecycle", color: "from-cyan-500 to-teal-500" },
  { name: "DPDP Act", desc: "India · 2023",      detail: "Digital Personal Data Protection Act — data fiduciary obligations, consent, breach notification, cross-border transfers", color: "from-orange-500 to-amber-500" },
  { name: "CERT-In",  desc: "Directions 2022",   detail: "CERT-In cyber security directions — incident reporting within 6 hours, log retention, IT infrastructure controls", color: "from-green-600 to-emerald-500" },
];

const FEATURES = [
  {
    icon: Zap,
    title: "AI compliance drift detection",
    desc: "After every evidence collection, AI compares control statuses against your baseline. The moment something degrades — a user loses MFA, a bucket goes public — your team gets an instant Slack or Teams alert with exactly what broke.",
  },
  {
    icon: ClipboardList,
    title: "AI questionnaire autofill",
    desc: "Paste any vendor security questionnaire — AI drafts answers grounded in 17 live data sources: your real integrations, policies, risks, vendors, incidents, RoPA, and more. Cut questionnaire time from days to minutes.",
  },
  {
    icon: BookOpen,
    title: "AI audit narrative generator",
    desc: "Generate a complete audit package with an AI-written narrative — covering your security posture, control coverage, and evidence quality — tailored to the specific framework you're being audited on.",
  },
  {
    icon: RefreshCw,
    title: "AI framework version monitor",
    desc: "TraceLayer monitors official regulation sources weekly. When any of the 9 frameworks updates — including DPDP Act and CERT-In — AI extracts the changed controls and queues them for your review — so you're never caught off guard.",
  },
  {
    icon: Plug,
    title: "120+ native integrations · simulate before you connect",
    desc: "Connect AWS, GitHub, Okta, Datadog, Snyk, and 95 more in minutes — no agents, no code. Before connecting anything, use the built-in simulation mode to see exactly what each integration adds to your score.",
  },
  {
    icon: Target,
    title: "Readiness Timeline",
    desc: "See your exact readiness score and a week-by-week estimate to audit-ready — with stage-specific next steps to close the gap fast.",
  },
  {
    icon: AlertTriangle,
    title: "Risk & Incident Management",
    desc: "Risk register with likelihood × impact scoring, incident tracker, vulnerability management, and pen test records — all linked to compliance controls.",
  },
  {
    icon: Shield,
    title: "GDPR Privacy Suite",
    desc: "Full GDPR toolkit: Records of Processing Activities (RoPA), Statement of Applicability, breach register, subject access request tracker, and management review records.",
  },
  {
    icon: BookOpen,
    title: "Policy Templates",
    desc: "Pre-written policies for SOC 2, ISO 27001, HIPAA, GDPR, and more. Customize and adopt in one click — incident response, BCP, vendor risk, and more.",
  },
  {
    icon: GraduationCap,
    title: "People Security Lifecycle",
    desc: "Training tracker, background check records, formal offboarding checklists — full HR security coverage from hire to departure for CC1.4 and beyond.",
  },
  {
    icon: Building2,
    title: "Vendor & Asset Management",
    desc: "Track vendors with risk tiers and SOC 2/ISO/HIPAA cert status. Maintain a live asset inventory with classification, environment, and ownership.",
  },
  {
    icon: UserCheck,
    title: "Access Reviews & BCP",
    desc: "Formal quarterly access reviews with sign-off and findings. BCP/DR plans with RTO/RPO targets and test history — audit-ready on demand.",
  },
  {
    icon: Globe,
    title: "Public Trust Center",
    desc: "Share a live compliance posture page with customers and investors — verified by TraceLayer, updated continuously, no manual upkeep.",
  },
  {
    icon: Database,
    title: "API keys for CI/CD",
    desc: "Push compliance evidence directly from your CI/CD pipelines — test results, deployment records, and security scans land in your evidence library automatically.",
  },
  {
    icon: Workflow,
    title: "Data Flow Map",
    desc: "Auto-maps every connected integration to its data types, storage region, risk level, and applicable regulations — GDPR, CCPA, HIPAA, PCI DSS. Pre-populates your RoPA on day one.",
  },
];

const HOW_IT_WORKS = [
  {
    step: "01",
    title: "Connect your tools",
    desc: "Paste an API key and evidence starts flowing immediately. No agents, no code, no week-long setup. Most teams are collecting evidence within 5 minutes — you can even simulate any integration first to preview your score before touching a credential.",
  },
  {
    step: "02",
    title: "We watch it for you",
    desc: "Three AI engines run quietly in the background. They collect evidence every 24 hours, alert you the moment a control breaks, and track regulation changes before they catch you off guard.",
  },
  {
    step: "03",
    title: "Share it with your auditor",
    desc: "Your readiness score updates automatically. When you're ready, generate a complete audit PDF in one click and share a read-only link straight to your auditor. That's it.",
  },
];

const TESTIMONIALS: { quote: string; author: string; role: string; stars: number }[] = [
];

const PAIN_POINTS = [
  { before: "Manually collecting evidence in spreadsheets",       after: "Evidence collected automatically every 24h from 120+ tools" },
  { before: "Finding out a control broke at the audit",           after: "Instant alert the moment anything goes wrong"              },
  { before: "Vendor questionnaires eating days of your time",     after: "AI drafts every answer from your live data in seconds"     },
  { before: "Mapping data flows by hand in a spreadsheet",        after: "Auto-mapped from your integrations on day one"             },
  { before: "GDPR buried across docs, emails, and spreadsheets",  after: "Privacy docs, breach log, and data map all in one place"   },
  { before: "Paying $50k+ for a compliance consultant",           after: "Full compliance program for $149/mo — no consultant needed"},
];


const FAQ = [
  {
    q: "How long does setup actually take?",
    a: "Honestly, under 5 minutes. Create an account, paste an API key for your first integration, and evidence collection starts right away. No agents to install, no code to write, no implementation project.",
  },
  {
    q: "Which compliance frameworks are supported?",
    a: "SOC 2 Type I & II, ISO 27001 (2022), HIPAA, GDPR, PCI DSS v4.0, CCPA, NIST CSF 2.0, DPDP Act 2023, and CERT-In Directions 2022. The same evidence you collect maps to all nine at once — connect your tools once and switch between framework views without doing any extra work.",
  },
  {
    q: "Does TraceLayer support DPDP Act and CERT-In compliance for Indian companies?",
    a: "Yes. TraceLayer has full coverage for India's Digital Personal Data Protection Act 2023 and CERT-In Directions 2022. DPDP Act controls cover lawful processing, data fiduciary obligations, data principal rights, breach notification (72-hour timeline), and cross-border transfer controls. CERT-In covers the 6-hour incident reporting requirement, IT infrastructure controls, log retention, identity verification, and endpoint security. Both frameworks are monitored weekly for regulatory updates.",
  },
  {
    q: "What does my readiness score mean?",
    a: "It's a live score that tells you how close you are to audit-ready — based on how much evidence you've collected, how fresh it is, and which controls still have gaps. It also shows a week-by-week estimate and specific next steps to close the gap faster.",
  },
  {
    q: "What tools can I connect?",
    a: "120+ integrations out of the box: AWS, GitHub, Slack, Google Workspace, Okta, Salesforce, Segment, HubSpot, Azure AD, Jira, GitLab, Datadog, CrowdStrike, Jamf, SentinelOne, Snyk, KnowBe4, Anthropic, OpenAI, and many more — each one pulling real evidence automatically.",
  },
  {
    q: "Does it handle security training and vendor reviews?",
    a: "Yes. You can assign security awareness training to your team by email, track who's completed it, and flag anyone overdue. For vendors, there's a full hub where you can track risk levels, certifications (SOC 2, ISO, HIPAA), and review dates.",
  },
  {
    q: "What are access reviews?",
    a: "Access reviews are formal quarterly reviews where you document who reviewed user access, what changed, and the outcome — all with a timestamp your auditor can rely on. TraceLayer walks you through it so nothing gets missed.",
  },
  {
    q: "Is my data safe? Do you store credentials?",
    a: "Yes, your credentials are encrypted before they ever touch our database. We use AES-256 symmetric encryption and never store or log plaintext secrets. Your data is isolated to your company — no one else can see it.",
  },
  {
    q: "Can I actually use this for a SOC 2 Type II audit?",
    a: "Yes, that's exactly what it's built for. TraceLayer collects continuous evidence with timestamps across your full observation period. When you're done, generate a formatted PDF and share a read-only link directly with your auditor.",
  },
  {
    q: "Is there really a free plan?",
    a: "Yes — no credit card, no time limit. The free plan includes SOC 2, automated evidence collection, risk register, policy templates, training tracker, vendor hub, and JSON reports for up to 3 integrations and 3 team members. Upgrade to Growth ($149/mo) for all 9 frameworks incl. DPDP Act & CERT-In, PDF reports, AI features, and Trust Center.",
  },
  {
    q: "What does the AI actually do?",
    a: "Three things: (1) It watches your controls and fires an instant Slack or Teams alert the moment something regresses. (2) It reads your live evidence and drafts answers to any security questionnaire a prospect sends you. (3) It monitors regulation sources weekly and flags any framework changes before they affect your audit.",
  },
  {
    q: "Does the AI write my audit report?",
    a: "Yes. One click generates a complete PDF with an AI-written narrative covering your security posture, control gaps, and evidence quality. It's formatted and ready to hand directly to your auditor.",
  },
];

const NAV_LINKS = [
  { href: "#how-it-works", label: "How it works" },
  { href: "#features",     label: "Features"     },
  { href: "#pricing",      label: "Pricing"      },
  { href: "/partners",     label: "Partners"     },
  { href: "#faq",          label: "FAQ"          },
  { href: "/tools",        label: "Free Tools"   },
  { href: "/blog",         label: "Blog"         },
];

const THEME = {
  "--bg": "#f7f1e8",
  "--ink": "#1f2937",
  "--muted": "#5b6472",
  "--accent": "#0f766e",
  "--accent-strong": "#0b5f59",
  "--accent-warm": "#f97316",
  "--card": "#ffffff",
} as CSSProperties;

// ── Marquee ───────────────────────────────────────────────────────────────────

function LogoPill({ name, logo }: { name: string; logo: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2.5 bg-white border border-black/6 rounded-2xl px-4 py-2.5 shadow-sm shrink-0">
      <span className="flex items-center justify-center w-6 h-6">{logo}</span>
      <span className="text-xs font-semibold text-gray-600 whitespace-nowrap">{name}</span>
    </div>
  );
}

function MarqueeRow({ reverse = false }: { reverse?: boolean }) {
  const items = [...INTEGRATION_LOGOS, ...INTEGRATION_LOGOS, ...INTEGRATION_LOGOS];
  return (
    <div className="overflow-hidden" style={{ maskImage: "linear-gradient(to right, transparent 0%, black 6%, black 94%, transparent 100%)" }}>
      <div
        className="flex gap-3 w-max"
        style={{ animation: `${reverse ? "marqueeRight" : "marqueeLeft"} 40s linear infinite` }}
      >
        {items.map((item, i) => (
          <LogoPill key={i} name={item.name} logo={item.logo} />
        ))}
      </div>
    </div>
  );
}

// ── FAQ Accordion ─────────────────────────────────────────────────────────────

function FaqAccordion({ items }: { items: typeof FAQ }) {
  const [open, setOpen] = useState<number | null>(null);
  return (
    <div className="space-y-2.5">
      {items.map((item, i) => (
        <div
          key={i}
          className={`rounded-2xl border transition-all duration-200 overflow-hidden ${
            open === i
              ? "bg-white border-[color:var(--accent)]/25 shadow-[0_4px_20px_rgba(15,118,110,0.08)]"
              : "bg-white/70 border-black/5 hover:border-black/10 hover:bg-white/90"
          }`}
        >
          <button
            className="w-full flex items-center justify-between gap-4 px-5 py-4 text-left"
            onClick={() => setOpen(open === i ? null : i)}
            aria-expanded={open === i}
          >
            <span className="font-semibold text-sm leading-snug text-[var(--ink)]">{item.q}</span>
            <ChevronDown
              className={`w-4 h-4 shrink-0 text-[var(--accent)] transition-transform duration-300 ${open === i ? "rotate-180" : ""}`}
            />
          </button>
          <div
            className="grid transition-all duration-300 ease-in-out"
            style={{ gridTemplateRows: open === i ? "1fr" : "0fr" }}
          >
            <div className="overflow-hidden">
              <p className="px-5 pb-5 text-sm text-[var(--muted)] leading-relaxed border-t border-black/5 pt-3">
                {item.a}
              </p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Animated stat counter ─────────────────────────────────────────────────────
function StatNumber({ value }: { value: string }) {
  const ref = useRef<HTMLParagraphElement>(null);
  const [displayed, setDisplayed] = useState("0");
  const [started, setStarted] = useState(false);

  // Parse "120+" → { num: 120, suffix: "+" }, "24h" → { num: 24, suffix: "h" }
  const match = value.match(/^(\d+)(.*)$/);
  const target = match ? parseInt(match[1]) : 0;
  const suffix = match ? match[2] : value;

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting && !started) setStarted(true); },
      { threshold: 0.5 }
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, [started]);

  useEffect(() => {
    if (!started) return;
    const duration = 1400;
    const startTime = Date.now();
    const timer = setInterval(() => {
      const progress = Math.min((Date.now() - startTime) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplayed(String(Math.round(target * eased)) + suffix);
      if (progress >= 1) clearInterval(timer);
    }, 16);
    return () => clearInterval(timer);
  }, [started, target, suffix]);

  return (
    <p ref={ref} className={`text-4xl md:text-5xl font-extrabold text-[var(--accent)] mb-1.5 leading-none ${started ? "stat-pop" : "opacity-0"}`}>
      {displayed}
    </p>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function LandingPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && user) router.replace("/dashboard");
  }, [user, loading, router]);

  const [checkoutLoading, setCheckoutLoading] = useState(false);

  const handleGrowthCta = async () => {
    if (user) {
      setCheckoutLoading(true);
      try {
        const { checkout_url } = await api.createCheckout();
        await openPaddleCheckout(checkout_url);
      } catch {
        router.push("/settings#billing");
      } finally {
        setCheckoutLoading(false);
      }
    } else {
      router.push("/register");
    }
  };

  const [mobileOpen, setMobileOpen] = useState(false);
  const [scrolled, setScrolled]     = useState(false);
  const [hidden, setHidden]         = useState(false);
  const [progress, setProgress]     = useState(0);
  const [newsletterEmail, setNewsletterEmail] = useState("");
  const [newsletterSent, setNewsletterSent]   = useState(false);
  const [newsletterLoading, setNewsletterLoading] = useState(false);

  const handleNewsletterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newsletterEmail) return;
    setNewsletterLoading(true);
    try {
      await fetch("/api/capture-lead", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: newsletterEmail, tool: "newsletter" }),
      });
      setNewsletterSent(true);
    } catch {
      setNewsletterSent(true); // Still show success
    } finally {
      setNewsletterLoading(false);
    }
  };
  const lastY = useRef(0);

  useEffect(() => {
    const onScroll = () => {
      const y = window.scrollY;
      const docH = document.documentElement.scrollHeight - window.innerHeight;
      setProgress(docH > 0 ? (y / docH) * 100 : 0);
      setScrolled(y > 20);
      setHidden(y > lastY.current && y > 120);
      lastY.current = y;
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  // Scroll-triggered fade-up animations
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) entry.target.classList.add("is-visible");
        });
      },
      { threshold: 0.1, rootMargin: "0px 0px -40px 0px" }
    );
    document.querySelectorAll("[data-animate], [data-stagger]").forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, []);

  const smoothScroll = (e: React.MouseEvent<HTMLAnchorElement>, href: string) => {
    if (!href.startsWith("#")) return;
    e.preventDefault();
    document.querySelector(href)?.scrollIntoView({ behavior: "smooth", block: "start" });
    setMobileOpen(false);
  };

  // Don't block render on auth check — redirect happens via useEffect once resolved.
  // Logged-in users see a brief flash then get pushed to /dashboard, which is fine.
  if (!loading && user) return null;

  return (
    <div
      className="min-h-screen bg-[var(--bg)] text-[var(--ink)]"
      style={THEME}
    >
      {/* Founding member announcement bar */}
      <div className="fixed top-0 left-0 right-0 w-full bg-[var(--accent)] text-white text-xs font-medium text-center py-1.5 px-4 z-[55] leading-snug">
        <span className="sm:hidden">$99/mo locked permanently — 100 spots.{" "}<Link href="/register" className="underline font-semibold">Claim →</Link></span>
        <span className="hidden sm:inline">Founding member offer: $99/mo locked permanently (normally $149) — first 100 customers only.{" "}<Link href="/register" className="underline font-semibold hover:opacity-80">Claim your spot →</Link></span>
      </div>

      {/* Scroll progress bar */}
      <div className="fixed top-0 left-0 right-0 h-[2px] z-[60] bg-transparent">
        <div className="h-full bg-[var(--accent)] transition-all duration-75" style={{ width: `${progress}%` }} />
      </div>

      {/* Nav */}
      <header
        className={`fixed top-[28px] left-0 right-0 z-50 transition-all duration-300 ${
          hidden ? "-translate-y-full" : "translate-y-0"
        } ${
          scrolled
            ? "bg-[#f7f1e8]/96 backdrop-blur-md shadow-sm border-b border-black/5"
            : "bg-[#f7f1e8]/70 backdrop-blur-sm"
        }`}
      >
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
          <a href="#" onClick={(e) => smoothScroll(e, "#")} className="flex items-center gap-2.5 shrink-0">
            <Image src="/logo-icon.png" alt="TraceLayer" width={30} height={30} className="rounded-lg" />
            <span className="font-extrabold text-base tracking-tight">TraceLayer</span>
          </a>

          <nav className="hidden md:flex items-center gap-1">
            {NAV_LINKS.map((l) =>
              l.href.startsWith("#") ? (
                <a
                  key={l.href}
                  href={l.href}
                  onClick={(e) => smoothScroll(e, l.href)}
                  className="text-sm text-[var(--muted)] hover:text-[var(--ink)] font-medium px-3 py-1.5 rounded-lg hover:bg-black/5 transition-all"
                >
                  {l.label}
                </a>
              ) : (
                <Link
                  key={l.href}
                  href={l.href}
                  className="text-sm font-semibold text-[var(--accent)] bg-[color:var(--accent)]/8 border border-[color:var(--accent)]/15 px-3 py-1.5 rounded-lg hover:bg-[color:var(--accent)]/15 transition-all"
                >
                  {l.label}
                </Link>
              )
            )}
          </nav>

          <div className="hidden md:flex items-center gap-2">
            <Link href="/login" className="text-sm text-[var(--muted)] hover:text-[var(--ink)] font-medium px-3 py-1.5 rounded-lg hover:bg-black/5 transition-all">
              Sign in
            </Link>
            <Link href="/register" className="text-sm bg-[var(--accent)] hover:bg-[var(--accent-strong)] text-white font-semibold px-4 py-1.5 rounded-lg transition-colors shadow-sm">
              Get started free
            </Link>
          </div>

          <button
            className="md:hidden p-2 rounded-lg hover:bg-black/5 transition-colors text-[var(--ink)]"
            onClick={() => setMobileOpen((v) => !v)}
            aria-label="Toggle menu"
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>

        {mobileOpen && (
          <div className="md:hidden bg-[color:var(--bg)]/98 backdrop-blur-md border-b border-black/5 px-6 py-4 space-y-1">
            {NAV_LINKS.map((l) =>
              l.href.startsWith("#") ? (
                <a
                  key={l.href}
                  href={l.href}
                  onClick={(e) => smoothScroll(e, l.href)}
                  className="block text-sm font-medium text-[var(--ink)] px-3 py-2.5 rounded-lg hover:bg-black/5 transition-colors"
                >
                  {l.label}
                </a>
              ) : (
                <Link
                  key={l.href}
                  href={l.href}
                  onClick={() => setMobileOpen(false)}
                  className="block text-sm font-semibold text-[var(--accent)] px-3 py-2.5 rounded-lg hover:bg-black/5 transition-colors"
                >
                  {l.label}
                </Link>
              )
            )}
            <div className="pt-3 border-t border-black/5 space-y-2">
              <Link href="/login" onClick={() => setMobileOpen(false)} className="block text-sm font-medium text-center text-[var(--muted)] px-3 py-2.5 rounded-lg border border-black/10 hover:bg-black/5 transition-colors">
                Sign in
              </Link>
              <Link href="/register" onClick={() => setMobileOpen(false)} className="block text-sm font-semibold text-center bg-[var(--accent)] hover:bg-[var(--accent-strong)] text-white px-3 py-2.5 rounded-lg transition-colors">
                Get started free
              </Link>
            </div>
          </div>
        )}
      </header>

      <div className="h-[80px] sm:h-[88px]" />

      {/* ── Hero ─────────────────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden">
        {/* Subtle grid pattern */}
        <div className="absolute inset-0 bg-[radial-gradient(#0f766e14_1px,transparent_1px)] [background-size:28px_28px]" />
        {/* Glow orbs */}
        <div className="absolute -top-40 right-0 h-[600px] w-[600px] rounded-full bg-[radial-gradient(circle,_rgba(15,118,110,0.22),_transparent_65%)] pointer-events-none animate-float-slow" />
        <div className="absolute -bottom-40 -left-20 h-[500px] w-[500px] rounded-full bg-[radial-gradient(circle,_rgba(249,115,22,0.13),_transparent_65%)] pointer-events-none animate-float-delay" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-[700px] w-[700px] rounded-full bg-[radial-gradient(circle,_rgba(15,118,110,0.05),_transparent_60%)] pointer-events-none" />
        {/* Floating decorative orbs */}
        <div className="absolute top-20 left-[8%] w-20 h-20 rounded-full bg-teal-400/20 blur-2xl pointer-events-none animate-float" />
        <div className="absolute top-40 right-[12%] w-14 h-14 rounded-full bg-emerald-400/25 blur-xl pointer-events-none animate-float-delay" />
        <div className="absolute bottom-32 left-[20%] w-16 h-16 rounded-full bg-teal-300/20 blur-2xl pointer-events-none animate-float-slow" />
        <div className="absolute top-60 right-[5%] w-10 h-10 rounded-full bg-orange-300/20 blur-xl pointer-events-none animate-float-delay" />
        <div className="absolute bottom-20 right-[22%] w-18 h-18 rounded-full bg-brand-400/15 blur-2xl pointer-events-none animate-float" />
        {/* Sweeping light beam */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-0 bottom-0 w-32 bg-gradient-to-r from-transparent via-white/[0.07] to-transparent animate-beam-sweep" />
        </div>

        <div className="max-w-6xl mx-auto px-6 pt-12 pb-8 text-center relative">
          {/* Announcement badge */}
          <div data-animate className="inline-flex items-center gap-2 bg-white/85 text-[var(--accent)] text-xs font-semibold px-3.5 py-1.5 rounded-full mb-4 border border-black/5 shadow-sm">
            <span className="relative flex h-2 w-2 shrink-0">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
            Full compliance platform — SOC 2, ISO 27001, DPDP Act, CERT-In & 5 more
          </div>

          <h1 data-animate data-delay="100" className="text-4xl sm:text-5xl md:text-[56px] font-extrabold leading-[1.1] mb-4 tracking-tight">
            Stop chasing compliance.<br />
            <span className="gradient-flow">
              Let it run itself.
            </span>
          </h1>

          <p data-animate data-delay="200" className="text-base sm:text-lg text-[var(--muted)] max-w-2xl mx-auto mb-6 leading-relaxed">
            Connect your tools once — evidence collects itself across SOC 2, ISO 27001, DPDP Act, CERT-In and 5 more frameworks. Alerts fire the moment something breaks, audit report is one click away.
          </p>

          <div data-animate data-delay="300" className="flex items-center justify-center gap-3 flex-wrap mb-4">
            <Link
              href="/register"
              className="relative inline-flex items-center gap-2 bg-[var(--accent)] hover:bg-[var(--accent-strong)] text-white font-semibold px-7 py-3.5 rounded-xl transition-colors text-sm overflow-hidden group shadow-[0_0_28px_rgba(15,118,110,0.35)] hover:shadow-[0_0_36px_rgba(15,118,110,0.55)]"
            >
              <span className="absolute inset-0 bg-gradient-to-r from-transparent via-white/15 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700" />
              Start for free
              <ArrowRight className="w-4 h-4" />
            </Link>
            <a
              href="https://calendly.com/nemanja-tracelayer/tracelayer-demo"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 border border-black/12 hover:border-[var(--accent)]/40 bg-white/60 hover:bg-white/90 text-[var(--ink)] font-semibold px-7 py-3.5 rounded-xl transition-all text-sm"
            >
              Book a 15-min demo
            </a>
          </div>

          <p className="text-xs text-[var(--muted)] mb-5">Free to start · Growth plan from <span className="font-semibold text-[var(--ink)]">$149/mo</span> · Not $20,000/year like Vanta</p>

          {/* Trust strip */}
          <div className="flex items-center justify-center flex-wrap gap-x-6 gap-y-1.5 text-xs text-[var(--muted)] mb-6">
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
              Free forever — no credit card
            </span>
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
              SOC 2 free — upgrade for all 9 frameworks incl. DPDP Act & CERT-In
            </span>
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
              Audit-ready in 2 weeks, not 9 months
            </span>
          </div>

          {/* ICP callout — who this is for */}
          <div className="inline-flex flex-wrap items-center justify-center gap-2 mb-8">
            {[
              "Seed & Series A/B CTOs",
              "Indian startups & SaaS",
              "DPDP Act compliance",
              "No compliance team yet",
              "Tired of $20K Vanta quotes",
            ].map((tag) => (
              <span key={tag} className="text-[11px] font-semibold text-[var(--accent)] bg-[var(--accent)]/8 border border-[var(--accent)]/20 px-3 py-1 rounded-full">
                {tag}
              </span>
            ))}
          </div>

          {/* Dashboard preview */}
          <div className="max-w-4xl mx-auto">
            <div className="bg-[#f3ede3] rounded-2xl border border-black/8 shadow-[0_24px_80px_rgba(15,23,42,0.12)] overflow-hidden relative max-h-[460px] sm:max-h-[520px]">

              {/* Browser chrome */}
              <div className="flex items-center gap-1.5 px-4 py-2.5 border-b border-black/8 bg-[#f3ede3]">
                <div className="w-2.5 h-2.5 rounded-full bg-red-400" />
                <div className="w-2.5 h-2.5 rounded-full bg-yellow-400" />
                <div className="w-2.5 h-2.5 rounded-full bg-green-400" />
                <div className="flex-1 mx-4">
                  <div className="bg-white/80 border border-black/10 rounded-md px-3 py-1 text-[11px] text-gray-400 font-mono hidden sm:block max-w-[240px] mx-auto text-center">
                    app.tracelayer.it.com/dashboard
                  </div>
                </div>
              </div>

              {/* Dashboard body */}
              <div className="p-3 space-y-2">

                {/* Page header */}
                <div className="flex items-center justify-between px-1">
                  <div>
                    <p className="text-sm font-bold text-gray-900">Dashboard</p>
                    <p className="text-[10px] text-gray-400">Sunday, March 22</p>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="text-[10px] bg-white border border-gray-200 px-2.5 py-1 rounded-lg text-gray-600 font-medium">Report</span>
                    <span className="text-[10px] bg-teal-600 text-white px-2.5 py-1 rounded-lg font-semibold">View compliance</span>
                  </div>
                </div>

                {/* Hero row: dark score card (2/3) + mini stats (1/3) */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">

                  {/* Dark score card */}
                  <div className="sm:col-span-2 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-xl p-3 overflow-hidden relative">
                    <div className="absolute top-0 left-1/2 -translate-x-1/2 w-48 h-20 bg-teal-500/10 rounded-full blur-2xl pointer-events-none" />
                    {/* Top: ring + score + tabs */}
                    <div className="flex items-start gap-3 mb-3">
                      <div className="relative shrink-0 w-14 h-14">
                        <svg className="w-14 h-14 -rotate-90" viewBox="0 0 56 56">
                          <circle cx="28" cy="28" r="22" fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="6"/>
                          <circle cx="28" cy="28" r="22" fill="none" stroke="#10b981" strokeWidth="6"
                            strokeDasharray={`${2*Math.PI*22}`} strokeDashoffset={`${2*Math.PI*22*0.06}`} strokeLinecap="round"/>
                        </svg>
                        <div className="absolute inset-0 flex flex-col items-center justify-center">
                          <span className="text-sm font-black text-white leading-none">94</span>
                          <span className="text-[8px] text-white/40">/100</span>
                        </div>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-[10px] text-white/50 mb-0.5">Compliance score</p>
                        <div className="flex items-center gap-2 mb-1.5">
                          <span className="text-2xl font-black text-white leading-none">94<span className="text-sm text-white/30">%</span></span>
                          <span className="text-[9px] font-bold bg-emerald-500/20 text-emerald-400 px-1.5 py-0.5 rounded-full">+0% vs prev</span>
                        </div>
                        <div className="flex gap-1 flex-wrap">
                          {["SOC 2","ISO 27001","HIPAA","GDPR","PCI DSS","CCPA","NIST CSF","DPDP","CERT-In"].map((fw,i) => (
                            <span key={fw} className={`text-[9px] font-semibold px-1.5 py-0.5 rounded-md whitespace-nowrap ${i===0?"bg-white text-slate-900":"text-white/40"}`}>{fw}</span>
                          ))}
                        </div>
                      </div>
                    </div>
                    {/* Bottom: 3 stat circles */}
                    <div className="grid grid-cols-3 gap-2 pt-2 border-t border-white/10">
                      {[
                        { label:"PASSING", sub:"of 3", value:"3", color:"#10b981", stroke:"#10b981" },
                        { label:"FAILING",  sub:"none",  value:"0", color:"rgba(255,255,255,0.2)", stroke:"rgba(255,255,255,0.12)" },
                        { label:"SCORE",   sub:"out of 100", value:"94", color:"#818cf8", stroke:"#818cf8" },
                      ].map((s) => (
                        <div key={s.label} className="flex flex-col items-center gap-1">
                          <div className="relative w-10 h-10">
                            <svg className="w-10 h-10 -rotate-90" viewBox="0 0 40 40">
                              <circle cx="20" cy="20" r="15" fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="4"/>
                              <circle cx="20" cy="20" r="15" fill="none" stroke={s.stroke} strokeWidth="4"
                                strokeDasharray={`${2*Math.PI*15}`} strokeDashoffset={`${2*Math.PI*15*(1-(s.label==="SCORE"?0.94:s.label==="PASSING"?0.3:0))}`} strokeLinecap="round"/>
                            </svg>
                            <div className="absolute inset-0 flex items-center justify-center">
                              <span className="text-xs font-black" style={{color:s.color}}>{s.value}</span>
                            </div>
                          </div>
                          <p className="text-[8px] font-bold text-white/40 uppercase tracking-wide">{s.label}</p>
                          <p className="text-[8px] text-white/20">{s.sub}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Mini stats column */}
                  <div className="grid grid-cols-2 sm:grid-cols-1 gap-1.5">
                    {[
                      { value:"211",   label:"Evidence records",   sub:"across all integrations", color:"text-gray-900" },
                      { value:"38",    label:"Active integrations", sub:"of 38 connected",         color:"text-teal-600" },
                      { value:"3",     label:"Controls monitored",  sub:"SOC 2 framework",         color:"text-gray-900" },
                      { value:"0",     label:"Action items",        sub:"All controls passing",    color:"text-gray-900" },
                    ].map((s) => (
                      <div key={s.label} className="bg-white rounded-xl border border-gray-100 px-3 py-2">
                        <p className={`text-base font-black ${s.color} leading-none mb-0.5`}>{s.value}</p>
                        <p className="text-[10px] font-medium text-gray-600">{s.label}</p>
                        <p className="text-[9px] text-gray-400">{s.sub}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Charts row: score trend + evidence activity */}
                <div className="hidden sm:grid grid-cols-2 gap-2">
                  <div className="bg-white rounded-xl border border-gray-100 p-3">
                    <div className="flex items-center justify-between mb-0.5">
                      <span className="text-[11px] font-semibold text-gray-800">Score trend</span>
                      <span className="text-[10px] font-bold text-emerald-600">↑0pts</span>
                    </div>
                    <p className="text-[9px] text-gray-400 mb-2">Last 30 days · SOC 2</p>
                    <svg viewBox="0 0 200 50" className="w-full h-10">
                      <defs>
                        <linearGradient id="lp-sg" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#10b981" stopOpacity="0.25"/>
                          <stop offset="100%" stopColor="#10b981" stopOpacity="0"/>
                        </linearGradient>
                      </defs>
                      <line x1="0" y1="6" x2="200" y2="6" stroke="#e5e7eb" strokeWidth="0.8" strokeDasharray="3,2"/>
                      <path d="M0,46 L80,46 L100,42 L120,38 L150,8 L175,6 L200,6 L200,50 L0,50Z" fill="url(#lp-sg)"/>
                      <path d="M0,46 L80,46 L100,42 L120,38 L150,8 L175,6 L200,6" fill="none" stroke="#10b981" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </div>
                  <div className="bg-white rounded-xl border border-gray-100 p-3">
                    <div className="flex items-center justify-between mb-0.5">
                      <span className="text-[11px] font-semibold text-gray-800">Evidence activity</span>
                      <span className="text-[10px] text-gray-400">211 records</span>
                    </div>
                    <p className="text-[9px] text-gray-400 mb-2">Last 14 days · per day</p>
                    <svg viewBox="0 0 200 50" className="w-full h-10">
                      {[
                        [10,48],[30,48],[50,48],[70,48],[90,46],[110,44],[130,42],[150,20],[170,6],[190,6]
                      ].map(([x,y],i) => (
                        <rect key={i} x={x-8} y={y} width="14" height={50-y}
                          fill={i===9?"#0f766e":"#e5e7eb"} rx="2"/>
                      ))}
                    </svg>
                  </div>
                </div>

                {/* Control breakdown */}
                <div className="bg-white rounded-xl border border-gray-100 p-3">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[11px] font-semibold text-gray-800">Control breakdown</span>
                    <span className="text-[10px] text-teal-600 font-semibold">Full view →</span>
                  </div>
                  {[
                    { name:"Access Control",       status:"Passing", score:95,  records:75  },
                    { name:"Logging & Monitoring",  status:"Passing", score:100, records:211 },
                    { name:"Change Management",     status:"Passing", score:83,  records:38  },
                  ].map((c) => (
                    <div key={c.name} className="mb-2 last:mb-0">
                      <div className="flex items-center justify-between text-[10px] mb-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-gray-700">{c.name}</span>
                          <span className="text-emerald-600 font-semibold">{c.status}</span>
                        </div>
                        <div className="flex items-center gap-2 text-gray-400">
                          <span>{c.records} records</span>
                          <span className="font-bold text-gray-800">{c.score}%</span>
                        </div>
                      </div>
                      <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                        <div className="h-full bg-emerald-500 rounded-full" style={{width:`${c.score}%`}}/>
                      </div>
                    </div>
                  ))}
                </div>

              </div>

              {/* Bottom fade */}
              <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-[#f3ede3] to-transparent pointer-events-none" />
            </div>

            {/* Live sync pill */}
            <div className="flex justify-center mt-4">
              <div className="inline-flex items-center gap-2 bg-white/90 backdrop-blur rounded-full px-4 py-2 shadow-md border border-black/5 text-xs">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shrink-0" />
                <span className="text-gray-500">Evidence synced</span>
                <span className="font-semibold text-gray-900">3 minutes ago</span>
                <span className="text-gray-300">·</span>
                <span className="text-gray-500">Next run in <span className="font-semibold text-gray-900">21h</span></span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Who it's for ──────────────────────────────────────────────────────── */}
      <section className="bg-white/60 border-y border-black/5 py-10">
        <div className="max-w-5xl mx-auto px-6">
          <p className="text-center text-xs font-bold text-[var(--muted)] uppercase tracking-widest mb-6">You&apos;re in the right place if…</p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {[
              {
                icon: Building2,
                heading: "An enterprise prospect asked for SOC 2, ISO 27001, or DPDP Act",
                body: "Your deal is on hold until security review clears. You need to get certified fast — not in 9 months, not for $20K.",
              },
              {
                icon: Users,
                heading: "You're a CTO or founder at an Indian SaaS or global startup",
                body: "Selling to enterprises in India or abroad — DPDP Act, CERT-In, ISO 27001, SOC 2. One platform covers all of them simultaneously.",
              },
              {
                icon: Zap,
                heading: "You need results without a consultant",
                body: "No ₹25,000/hr vCISO, no months-long implementation project. Connect your tools today, evidence starts collecting tonight.",
              },
            ].map(({ icon: Icon, heading, body }) => (
              <div key={heading} className="flex gap-4 p-5 rounded-2xl border border-black/5 bg-[var(--card)] shadow-[0_2px_12px_rgba(15,23,42,0.04)]">
                <div className="w-9 h-9 rounded-xl bg-[var(--accent)]/10 flex items-center justify-center shrink-0 mt-0.5">
                  <Icon className="w-4 h-4 text-[var(--accent)]" />
                </div>
                <div>
                  <p className="text-sm font-bold text-[var(--ink)] mb-1 leading-snug">{heading}</p>
                  <p className="text-xs text-[var(--muted)] leading-relaxed">{body}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Integrations marquee ──────────────────────────────────────────────── */}
      <section className="py-10 overflow-hidden border-y border-black/5 bg-white/50">
        <p className="text-center text-[11px] text-[var(--muted)] font-bold uppercase tracking-widest mb-6">
          Integrates with the tools you already use
        </p>
        <MarqueeRow />
      </section>

      {/* ── Free tools nudge ─────────────────────────────────────────────────── */}
      <section className="bg-[var(--bg)] py-5 border-b border-black/5">
        <div className="max-w-4xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-3">
          <p className="text-xs text-[var(--muted)]">
            <span className="font-semibold text-[var(--ink)]">Not sure where to start?</span>{" "}
            Four free tools — no account needed. Know your risk before spending a dollar.
          </p>
          <Link href="/tools" className="shrink-0 inline-flex items-center gap-1.5 text-xs font-semibold text-[var(--accent)] hover:underline">
            Explore free tools <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </section>

      {/* ── Stats ─────────────────────────────────────────────────────────────── */}
      <section className="bg-white/60 py-12 border-b border-black/5">
        <div className="max-w-4xl mx-auto px-6 grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
          {STATS.map((s) => (
            <div key={s.label} className="group cursor-default">
              <StatNumber value={s.value} />
              <p className="text-xs text-[var(--muted)] font-semibold">{s.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── AI Engines ────────────────────────────────────────────────────────── */}
      <section className="py-20 bg-gradient-to-b from-slate-900 to-slate-800 relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(#0f766e18_1px,transparent_1px)] [background-size:32px_32px]" />
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[200px] bg-[radial-gradient(circle,rgba(15,118,110,0.25),transparent_70%)] pointer-events-none" />
        <div className="max-w-6xl mx-auto px-6 relative">
          <div className="text-center mb-14" data-animate>
            <div className="inline-flex items-center gap-2 bg-teal-900/40 text-teal-400 text-xs font-semibold px-3.5 py-1.5 rounded-full mb-4 border border-teal-700/30">
              <span className="relative flex h-2 w-2 shrink-0">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-teal-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-teal-500" />
              </span>
              Three AI engines, always running
            </div>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-white mb-4 tracking-tight">
              AI that works while you sleep
            </h2>
            <p className="text-slate-400 max-w-xl mx-auto text-sm leading-relaxed">
              TraceLayer doesn&apos;t just collect evidence — it watches over it. Three AI engines run quietly in the background so you&apos;re never blindsided by a broken control or an auditor question you can&apos;t answer.
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-5">
            {[
              {
                number: "01",
                color: "from-teal-500 to-emerald-500",
                bg: "bg-teal-900/20 border-teal-700/20",
                title: "Drift Detection",
                subtitle: "Fires within minutes",
                desc: "After every evidence collection, AI compares each control's status to its last known baseline. The moment something degrades — MFA disabled, a bucket goes public, an integration breaks — your Slack or Teams channel gets an immediate alert with the exact control, framework, and what triggered it.",
                bullets: ["Compares every control after each sync", "Instant Slack + Teams alerts", "Tracks regressions and recoveries"],
              },
              {
                number: "02",
                color: "from-violet-500 to-purple-500",
                bg: "bg-violet-900/20 border-violet-700/20",
                title: "Questionnaire AI",
                subtitle: "Days → minutes",
                desc: "Paste any enterprise security questionnaire. AI reads your live evidence — 89+ integrations, policies, risks, incidents, vendors, RoPA — and drafts every answer grounded in your actual security posture. You review and send. No generic boilerplate.",
                bullets: ["Reads 17+ live data sources", "Grounded in your real evidence", "Exports in the customer's format"],
              },
              {
                number: "03",
                color: "from-amber-500 to-orange-500",
                bg: "bg-amber-900/20 border-amber-700/20",
                title: "Framework Monitor",
                subtitle: "Weekly, automated",
                desc: "AI monitors official sources for SOC 2, ISO 27001, HIPAA, GDPR, PCI DSS, CCPA, NIST CSF, DPDP Act, and CERT-In every week. When a framework updates, AI extracts the changed controls, summarizes what changed, and queues a review — so you're always on the latest version.",
                bullets: ["Monitors 9 regulatory sources", "AI-extracts control changes", "Human review before applying"],
              },
            ].map((engine, i) => (
              <div
                key={engine.number}
                data-animate
                data-delay={String(i * 150)}
                className={`spotlight rounded-2xl border p-6 ${engine.bg} flex flex-col gap-4 hover:-translate-y-1 transition-transform duration-300`}
                onMouseMove={(e) => {
                  const r = e.currentTarget.getBoundingClientRect();
                  e.currentTarget.style.setProperty("--mouse-x", `${e.clientX - r.left}px`);
                  e.currentTarget.style.setProperty("--mouse-y", `${e.clientY - r.top}px`);
                }}
              >
                <div className="flex items-start justify-between">
                  <div className={`text-3xl font-black bg-gradient-to-r ${engine.color} bg-clip-text text-transparent leading-none`}>
                    {engine.number}
                  </div>
                  <span className="text-[10px] font-semibold text-slate-400 bg-slate-800/60 px-2 py-1 rounded-full border border-slate-700/40">
                    {engine.subtitle}
                  </span>
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white mb-2">{engine.title}</h3>
                  <p className="text-sm text-slate-400 leading-relaxed">{engine.desc}</p>
                </div>
                <ul className="space-y-1.5 mt-auto">
                  {engine.bullets.map((b) => (
                    <li key={b} className="flex items-center gap-2 text-xs text-slate-300">
                      <CheckCircle2 className="w-3.5 h-3.5 text-teal-400 shrink-0" />
                      {b}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── How it works ──────────────────────────────────────────────────────── */}
      <section id="how-it-works" className="scroll-mt-16 max-w-6xl mx-auto px-6 py-14 md:py-22">
        <div data-animate className="text-center mb-12 md:mb-16">
          <p className="text-xs font-bold text-[var(--accent)] uppercase tracking-widest mb-2">How it works</p>
          <h2 className="text-2xl md:text-4xl font-extrabold">Up and running in minutes</h2>
          <p className="text-[var(--muted)] mt-3 text-sm max-w-lg mx-auto leading-relaxed">
            No implementation project. No consultants. Just connect your tools and watch your compliance program build itself.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-12 md:gap-8 relative">
          {/* Connector line on desktop */}
          <div className="hidden md:block absolute top-8 left-[16.67%] right-[16.67%] h-px bg-gradient-to-r from-transparent via-[color:var(--accent)]/20 to-transparent" />
          {HOW_IT_WORKS.map((item, i) => (
            <div key={item.step} data-animate data-delay={String(i * 100 + 100)} className="text-center relative">
              <div className="w-16 h-16 rounded-2xl bg-white border border-black/5 shadow-[0_4px_20px_rgba(15,23,42,0.06)] flex items-center justify-center mx-auto mb-5">
                <span className="text-2xl font-black text-[var(--accent)]">{item.step}</span>
              </div>
              <h3 className="text-base font-bold mb-2.5">{item.title}</h3>
              <p className="text-sm text-[var(--muted)] leading-relaxed max-w-[260px] mx-auto">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Module grid ───────────────────────────────────────────────────────── */}
      <section className="bg-white/60 py-12 md:py-18 border-y border-black/5">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-10">
            <p className="text-xs font-bold text-[var(--accent)] uppercase tracking-widest mb-2">Complete platform</p>
            <h2 className="text-2xl md:text-4xl font-extrabold">Everything your compliance program needs</h2>
            <p className="text-[var(--muted)] mt-3 text-sm max-w-lg mx-auto leading-relaxed">
              Not just evidence collection — a complete compliance program. Evidence, risk, privacy, people, vendors, AI, and reporting, all in one place.
            </p>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {[
              { icon: Zap,           label: "Evidence Collection",  desc: "Automated, 24h"          },
              { icon: BarChart3,     label: "Compliance Score",     desc: "Real-time"               },
              { icon: Target,        label: "Readiness Timeline",   desc: "Weeks to audit"          },
              { icon: AlertTriangle, label: "Risk Register",        desc: "CC3 & CC9"               },
              { icon: Siren,         label: "Incident Management",  desc: "Track & resolve"         },
              { icon: BookOpen,      label: "Policy Templates",     desc: "Pre-written"             },
              { icon: GraduationCap, label: "Training Tracker",     desc: "CC1.4 evidence"          },
              { icon: Shield,        label: "Pen Test Tracker",     desc: "Annual requirement"      },
              { icon: Building2,     label: "Vendor Diligence",     desc: "CC9.2"                   },
              { icon: UserCheck,     label: "Access Reviews",       desc: "CC6.3 sign-off"          },
              { icon: Server,        label: "Asset Inventory",      desc: "CC6.1 / CC6.7"           },
              { icon: Bug,           label: "Vulnerability Mgmt",   desc: "Severity tracking"       },
              { icon: RefreshCw,     label: "Business Continuity",  desc: "BCP/DR + RTO/RPO"        },
              { icon: Workflow,      label: "Data Flow Map",        desc: "Auto-mapped, GDPR-ready" },
              { icon: Database,      label: "GDPR Privacy Suite",   desc: "RoPA, SoA, Breaches"     },
              { icon: ClipboardList, label: "AI Questionnaire",     desc: "17 data sources"         },
              { icon: Globe,         label: "Trust Page",           desc: "Live public page"        },
              { icon: FileText,      label: "Audit Reports",        desc: "PDF & JSON"              },
              { icon: Sparkles,      label: "AI Audit Package",     desc: "AI narrative PDF"        },
              { icon: ClipboardCheck,label: "Management Reviews",   desc: "Leadership sign-off"     },
              { icon: Lock,          label: "Auditor Portal",       desc: "Read-only access"        },
              { icon: Users,         label: "Team RBAC",            desc: "Admin & member"          },
              { icon: Network,       label: "CI/CD Ingest",         desc: "Push from pipelines"     },
              { icon: Plug,          label: "120+ Integrations",    desc: "Salesforce, AWS, Okta…"  },
            ].map(({ icon: Icon, label, desc }, i) => (
              <div
                key={label}
                data-stagger
                style={{ transitionDelay: `${i * 35}ms` }}
                className="spotlight bg-[var(--card)] rounded-2xl border border-black/5 p-4 hover:shadow-[0_8px_24px_rgba(15,23,42,0.08)] hover:-translate-y-1 transition-all duration-200 group"
                onMouseMove={(e) => {
                  const r = e.currentTarget.getBoundingClientRect();
                  e.currentTarget.style.setProperty("--mouse-x", `${e.clientX - r.left}px`);
                  e.currentTarget.style.setProperty("--mouse-y", `${e.clientY - r.top}px`);
                }}
              >
                <div className="w-8 h-8 bg-[color:var(--accent)]/10 rounded-xl flex items-center justify-center mb-3 group-hover:bg-[color:var(--accent)]/20 transition-colors group-hover:scale-110 duration-200">
                  <Icon className="w-4 h-4 text-[var(--accent)]" />
                </div>
                <p className="text-xs font-bold text-[var(--ink)] leading-snug">{label}</p>
                <p className="text-[10px] text-[var(--muted)] mt-0.5">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Data Flow Map ─────────────────────────────────────────────────────── */}
      <section className="py-16 md:py-24 bg-white border-y border-black/5">
        <div className="max-w-6xl mx-auto px-6">
          <div data-animate className="text-center mb-12">
            <div className="inline-flex items-center gap-2 bg-teal-50 text-teal-700 text-xs font-semibold px-3.5 py-1.5 rounded-full mb-4 border border-teal-100">
              <Workflow className="w-3.5 h-3.5" />
              New — Data Flow Mapping
            </div>
            <h2 className="text-2xl md:text-4xl font-extrabold text-[var(--ink)]">Know exactly where your data goes</h2>
            <p className="text-[var(--muted)] mt-3 text-sm max-w-xl mx-auto leading-relaxed">
              TraceLayer reads your connected tools and maps every data type to where it lives, who processes it, and which regulations apply. No spreadsheet. No guesswork. Your privacy docs are ready before you ask for them.
            </p>
          </div>

          {/* Flow visualization */}
          <div className="flex flex-col md:flex-row items-stretch justify-center gap-0 md:gap-3 mb-10" data-animate>
            {/* Data */}
            <div className="bg-blue-50 border border-blue-100 rounded-2xl p-4 md:p-5 w-full md:flex-1 md:max-w-[180px]">
              <p className="text-[10px] font-bold text-blue-500 uppercase tracking-widest mb-3">Data</p>
              {["Email address", "Health records", "Payment info", "Device ID", "Location data"].map((d) => (
                <div key={d} className="flex items-center gap-2 mb-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-blue-400 shrink-0" />
                  <span className="text-xs text-blue-800 font-medium leading-tight">{d}</span>
                </div>
              ))}
            </div>
            <div className="flex items-center justify-center shrink-0 py-1 md:py-0">
              <ArrowRight className="hidden md:block w-4 h-4 text-gray-300" />
              <ChevronDown className="block md:hidden w-4 h-4 text-gray-300" />
            </div>
            {/* Tools */}
            <div className="bg-[color:var(--accent)]/5 border border-[color:var(--accent)]/10 rounded-2xl p-4 md:p-5 w-full md:flex-1 md:max-w-[180px]">
              <p className="text-[10px] font-bold text-[var(--accent)] uppercase tracking-widest mb-3">Tools</p>
              {["Salesforce", "Segment", "Stripe", "Google Analytics", "HubSpot"].map((t) => (
                <div key={t} className="flex items-center gap-2 mb-2">
                  <div className="w-4 h-4 rounded bg-[color:var(--accent)]/15 flex items-center justify-center shrink-0">
                    <Plug className="w-2.5 h-2.5 text-[var(--accent)]" />
                  </div>
                  <span className="text-xs text-[var(--ink)] font-medium">{t}</span>
                </div>
              ))}
            </div>
            <div className="flex items-center justify-center shrink-0 py-1 md:py-0">
              <ArrowRight className="hidden md:block w-4 h-4 text-gray-300" />
              <ChevronDown className="block md:hidden w-4 h-4 text-gray-300" />
            </div>
            {/* Region */}
            <div className="bg-amber-50 border border-amber-100 rounded-2xl p-4 md:p-5 w-full md:flex-1 md:max-w-[165px]">
              <p className="text-[10px] font-bold text-amber-600 uppercase tracking-widest mb-3">Region</p>
              {[["United States", "🇺🇸"], ["European Union", "🇪🇺"], ["India", "🇮🇳"], ["Global", "🌐"]].map(([r, flag]) => (
                <div key={r} className="flex items-center gap-1.5 mb-2.5">
                  <span className="text-sm leading-none">{flag}</span>
                  <span className="text-xs text-amber-800 font-medium">{r}</span>
                </div>
              ))}
            </div>
            <div className="flex items-center justify-center shrink-0 py-1 md:py-0">
              <ArrowRight className="hidden md:block w-4 h-4 text-gray-300" />
              <ChevronDown className="block md:hidden w-4 h-4 text-gray-300" />
            </div>
            {/* Risk */}
            <div className="bg-red-50 border border-red-100 rounded-2xl p-4 md:p-5 w-full md:flex-1 md:max-w-[150px]">
              <p className="text-[10px] font-bold text-red-500 uppercase tracking-widest mb-3">Risk</p>
              {[
                { label: "Critical", cls: "bg-red-100 text-red-700 border-red-200" },
                { label: "High",     cls: "bg-orange-100 text-orange-700 border-orange-200" },
                { label: "Medium",   cls: "bg-amber-100 text-amber-700 border-amber-200" },
                { label: "Low",      cls: "bg-emerald-100 text-emerald-700 border-emerald-200" },
              ].map(({ label, cls }) => (
                <div key={label} className={`text-[11px] font-semibold px-2 py-0.5 rounded-md mb-1.5 border inline-block ${cls}`}>{label}</div>
              ))}
            </div>
            <div className="flex items-center justify-center shrink-0 py-1 md:py-0">
              <ArrowRight className="hidden md:block w-4 h-4 text-gray-300" />
              <ChevronDown className="block md:hidden w-4 h-4 text-gray-300" />
            </div>
            {/* Regulations */}
            <div className="bg-purple-50 border border-purple-100 rounded-2xl p-4 md:p-5 w-full md:flex-1 md:max-w-[150px]">
              <p className="text-[10px] font-bold text-purple-500 uppercase tracking-widest mb-3">Regulations</p>
              {["GDPR", "CCPA", "HIPAA", "PCI DSS", "DPDP Act", "CERT-In"].map((r) => (
                <div key={r} className="flex items-center gap-1.5 mb-2">
                  <CheckCircle2 className="w-3 h-3 text-purple-500 shrink-0" />
                  <span className="text-xs text-purple-800 font-semibold">{r}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Three benefits — 3 columns, perfectly symmetric */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              {
                icon: Zap,
                title: "Auto-detected on connect",
                desc: "Connect Salesforce → TraceLayer instantly maps customer PII to GDPR, CCPA, and the US region. Every integration carries a pre-built data profile. Zero manual entry.",
              },
              {
                icon: AlertTriangle,
                title: "Risk-scored by default",
                desc: "Health data = critical. Payment data = critical. Cross-border transfers = elevated. Your highest privacy risks surface on day one, before your auditor asks.",
              },
              {
                icon: FileText,
                title: "RoPA pre-populated",
                desc: "Data flow records automatically feed your GDPR Article 30 Record of Processing Activities. Export as CSV for your DPO or auditor — no spreadsheet juggling.",
              },
            ].map(({ icon: Icon, title, desc }) => (
              <div key={title} className="bg-[var(--card)] border border-black/5 rounded-2xl p-5 shadow-[0_4px_16px_rgba(15,23,42,0.05)]">
                <div className="w-9 h-9 rounded-xl bg-[color:var(--accent)]/10 flex items-center justify-center mb-3">
                  <Icon className="w-4 h-4 text-[var(--accent)]" />
                </div>
                <h3 className="text-sm font-bold text-[var(--ink)] mb-1.5">{title}</h3>
                <p className="text-xs text-[var(--muted)] leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Locked markets section ────────────────────────────────────────────── */}
      <section className="py-14 md:py-20 bg-slate-950 overflow-hidden">
        <div className="max-w-5xl mx-auto px-6">
          <div className="text-center mb-10">
            <p className="text-xs font-bold text-rose-400 uppercase tracking-widest mb-3">The cost of waiting</p>
            <h2 className="text-2xl md:text-4xl font-extrabold text-white leading-tight mb-4">
              No compliance? Here&apos;s what you&apos;re<br className="hidden sm:block" />{" "}
              <span className="bg-gradient-to-r from-rose-400 to-orange-400 bg-clip-text text-transparent">not allowed to touch.</span>
            </h2>
            <p className="text-white/50 text-sm md:text-base max-w-2xl mx-auto leading-relaxed">
              Compliance isn&apos;t a checkbox — it&apos;s a market access key. Without it, entire verticals, contract types, and partner ecosystems are simply off the table.
            </p>
          </div>

          {/* Locked doors grid */}
          <div className="grid sm:grid-cols-2 gap-4 mb-10">
            {[
              {
                icon: Building2,
                market: "Enterprise deals",
                tag: "$100k+ ACV",
                desc: "78% of enterprise procurement teams require SOC 2 or ISO 27001 before a contract can be signed. Your deal gets paused at security review. Their compliant competitor closes it.",
              },
              {
                icon: Shield,
                market: "Indian enterprise & government",
                tag: "DPDP Act · CERT-In",
                desc: "Indian enterprises and government-adjacent contracts increasingly require DPDP Act compliance and CERT-In adherence. Non-compliant SaaS vendors are blocked from procurement and face penalty exposure under the Act.",
              },
              {
                icon: Lock,
                market: "Healthcare & life sciences",
                tag: "HIPAA required",
                desc: "Any vendor that touches PHI needs HIPAA compliance. No exceptions, no grace periods. The hospital legal team will not countersign until your BAA is backed by a real audit trail.",
              },
              {
                icon: Globe,
                market: "Partner & marketplace listings",
                tag: "Salesforce · AWS · Slack",
                desc: "AppExchange, AWS Marketplace, Slack App Directory — all require a passing security review or compliance certification to list. Without it, you're invisible to their customer bases.",
              },
            ].map(({ icon: Icon, market, tag, desc }) => (
              <div key={market} className="bg-white/4 border border-white/8 rounded-2xl p-6 hover:bg-white/6 transition-colors">
                <div className="flex items-start gap-4 mb-3">
                  <div className="w-9 h-9 rounded-xl bg-rose-500/15 border border-rose-500/20 flex items-center justify-center shrink-0">
                    <Icon className="w-4 h-4 text-rose-400" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-white">{market}</p>
                    <p className="text-xs text-rose-400/80 font-semibold mt-0.5">{tag}</p>
                  </div>
                </div>
                <p className="text-sm text-white/45 leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>

          {/* Bottom stat bar */}
          <div className="bg-white/4 border border-white/8 rounded-2xl p-5 grid grid-cols-1 sm:grid-cols-3 divide-y sm:divide-y-0 sm:divide-x divide-white/8 text-center">
            {[
              { stat: "$4.35M", label: "average cost of a data breach (IBM Security, 2024)" },
              { stat: "9 mo", label: "average time to SOC 2 done manually, without automation" },
              { stat: "3×", label: "more enterprise deals closed by SOC 2 certified startups" },
            ].map(({ stat, label }) => (
              <div key={stat} className="py-4 sm:py-2 sm:px-6 first:pt-0 last:pb-0 sm:first:pt-2 sm:last:pb-2">
                <p className="text-2xl font-extrabold text-rose-400 mb-1">{stat}</p>
                <p className="text-xs text-white/40 leading-snug">{label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Revenue Impact lead magnet ────────────────────────────────────────── */}
      <section className="py-14 md:py-20 bg-[var(--bg)]">
        <div className="max-w-5xl mx-auto px-6">
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-3xl overflow-hidden shadow-2xl">
            <div className="grid md:grid-cols-2 gap-0">
              {/* Left — copy */}
              <div className="p-8 md:p-12">
                <div className="inline-flex items-center gap-2 bg-orange-500/15 text-orange-400 text-xs font-bold px-3 py-1.5 rounded-full mb-5 border border-orange-500/20">
                  <TrendingDown className="w-3.5 h-3.5" />
                  Free calculator · No signup
                </div>
                <h2 className="text-2xl md:text-3xl font-extrabold text-white mb-3 leading-tight">
                  How much is non-compliance<br />
                  <span className="bg-gradient-to-r from-orange-400 to-rose-400 bg-clip-text text-transparent">costing your business?</span>
                </h2>
                <p className="text-white/60 text-sm leading-relaxed mb-6">
                  Answer 3 quick questions. See the exact dollar impact — blocked deals, fines exposure, and staff time — plus the ROI if you fix it today.
                </p>
                <Link
                  href="/tools/revenue-impact"
                  className="inline-flex items-center gap-2 bg-gradient-to-r from-orange-500 to-rose-500 hover:from-orange-600 hover:to-rose-600 text-white font-bold px-6 py-3 rounded-xl transition-all shadow-lg shadow-orange-500/25 text-sm"
                >
                  Calculate my risk <ArrowRight className="w-4 h-4" />
                </Link>
                <p className="text-white/30 text-xs mt-3">Takes 2 minutes · Free forever</p>
              </div>

              {/* Right — stat preview */}
              <div className="bg-white/5 border-l border-white/10 p-8 md:p-12 flex flex-col justify-center gap-5">
                {[
                  { stat: "78%", desc: "of enterprise buyers require SOC 2 before signing", color: "text-rose-400" },
                  { stat: "6 mo", desc: "average deal delay when compliance is missing", color: "text-orange-400" },
                  { stat: "12%", desc: "of eng team time lost to manual compliance work", color: "text-amber-400" },
                ].map((item) => (
                  <div key={item.stat} className="flex items-center gap-4">
                    <span className={`text-2xl font-extrabold shrink-0 ${item.color}`}>{item.stat}</span>
                    <p className="text-sm text-white/50 leading-snug">{item.desc}</p>
                  </div>
                ))}
                <div className="mt-2 pt-5 border-t border-white/10">
                  <p className="text-xs text-white/30">Based on industry data from Vanta, Drata, and Ponemon Institute research.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Before / After ────────────────────────────────────────────────────── */}
      <section className="bg-slate-900 py-14 md:py-22">
        <div className="max-w-5xl mx-auto px-6">
          <div className="text-center mb-10 md:mb-14">
            <p className="text-xs font-bold text-orange-400 uppercase tracking-widest mb-2">Sound familiar?</p>
            <h2 className="text-2xl md:text-4xl font-extrabold text-white">There&apos;s a better way to do this</h2>
          </div>
          <div className="grid md:grid-cols-2 gap-4">
            <div className="bg-white/5 rounded-2xl p-6 border border-white/8">
              <p className="text-xs font-bold text-red-400 uppercase tracking-widest mb-5">Before</p>
              <div className="space-y-3.5">
                {PAIN_POINTS.map((p) => (
                  <div key={p.before} className="flex items-start gap-3">
                    <div className="w-5 h-5 rounded-full bg-red-500/15 border border-red-500/20 flex items-center justify-center shrink-0 mt-0.5">
                      <X className="w-2.5 h-2.5 text-red-400" />
                    </div>
                    <p className="text-sm text-white/55 leading-snug">{p.before}</p>
                  </div>
                ))}
              </div>
            </div>
            <div className="bg-teal-500/10 rounded-2xl p-6 border border-teal-500/20">
              <p className="text-xs font-bold text-teal-400 uppercase tracking-widest mb-5">With TraceLayer</p>
              <div className="space-y-3.5">
                {PAIN_POINTS.map((p) => (
                  <div key={p.after} className="flex items-start gap-3">
                    <CheckCircle2 className="w-5 h-5 text-teal-400 shrink-0 mt-0.5" />
                    <p className="text-sm text-white/80 leading-snug">{p.after}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Features ──────────────────────────────────────────────────────────── */}
      <section id="features" className="scroll-mt-16 bg-white/60 py-14 md:py-22">
        <div className="max-w-6xl mx-auto px-6">
          <div data-animate className="text-center mb-10 md:mb-14">
            <p className="text-xs font-bold text-[var(--accent)] uppercase tracking-widest mb-2">Features</p>
            <h2 className="text-2xl md:text-4xl font-extrabold">A complete compliance program, not just a tool</h2>
            <p className="text-[var(--muted)] mt-3 text-sm max-w-lg mx-auto leading-relaxed">
              From the first integration you connect to the moment you hand your auditor a report — TraceLayer runs the whole thing automatically.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {FEATURES.map(({ icon: Icon, title, desc }, i) => (
              <div key={title} data-animate data-delay={String((i % 3) * 100 + 100)}
                className="rounded-2xl border bg-[var(--card)] border-black/5 p-6 shadow-[0_4px_20px_rgba(15,23,42,0.04)] hover:shadow-[0_8px_32px_rgba(15,23,42,0.08)] hover:-translate-y-0.5 transition-all duration-200"
              >
                <div className="w-10 h-10 bg-[color:var(--accent)]/10 rounded-xl flex items-center justify-center mb-4">
                  <Icon className="w-5 h-5 text-[var(--accent)]" />
                </div>
                <h3 className="font-bold mb-2 text-sm">{title}</h3>
                <p className="text-sm text-[var(--muted)] leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Security trust strip ───────────────────────────────────────────── */}
      <section className="py-10 border-y border-black/6 bg-white/40">
        <div className="max-w-5xl mx-auto px-6">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 items-center">
            <div className="flex flex-col items-center text-center gap-1.5">
              <Lock className="w-6 h-6 text-[var(--accent)]"/>
              <span className="text-xs font-semibold text-[var(--ink)]">Fernet-encrypted secrets</span>
              <span className="text-[11px] text-[var(--muted)]">All credentials AES-256 at rest</span>
            </div>
            <div className="flex flex-col items-center text-center gap-1.5">
              <Database className="w-6 h-6 text-[var(--accent)]"/>
              <span className="text-xs font-semibold text-[var(--ink)]">Supabase PostgreSQL</span>
              <span className="text-[11px] text-[var(--muted)]">Isolated per-company data</span>
            </div>
            <div className="flex flex-col items-center text-center gap-1.5">
              <ShieldCheck className="w-6 h-6 text-[var(--accent)]"/>
              <span className="text-xs font-semibold text-[var(--ink)]">API key CI/CD integration</span>
              <span className="text-[11px] text-[var(--muted)]">Push evidence from your pipelines</span>
            </div>
            <div className="flex flex-col items-center text-center gap-1.5">
              <Globe className="w-6 h-6 text-[var(--accent)]"/>
              <span className="text-xs font-semibold text-[var(--ink)]">Live Trust Center</span>
              <span className="text-[11px] text-[var(--muted)]">Share compliance posture publicly</span>
            </div>
          </div>
        </div>
      </section>

      {/* ── Second marquee ────────────────────────────────────────────────────── */}
      <section className="py-10 overflow-hidden border-y border-black/5 bg-white/40">
        <MarqueeRow reverse />
      </section>

      {/* ── Frameworks ────────────────────────────────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-6 py-14 md:py-22">
        <div data-animate className="text-center mb-10 md:mb-14">
          <p className="text-xs font-bold text-[var(--accent)] uppercase tracking-widest mb-2">Frameworks</p>
          <h2 className="text-2xl md:text-4xl font-extrabold">Nine frameworks, one platform</h2>
          <p className="text-[var(--muted)] mt-3 text-sm max-w-lg mx-auto leading-relaxed">
            Connect your tools once and your evidence maps to every framework simultaneously — SOC 2, ISO 27001, DPDP Act, CERT-In, GDPR, HIPAA, PCI DSS, CCPA, NIST CSF. Switch views without reconnecting anything.
          </p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {FRAMEWORKS.map((f) => (
            <div key={f.name} className="bg-[var(--card)] border border-black/5 rounded-2xl p-5 shadow-[0_4px_16px_rgba(15,23,42,0.05)] hover:shadow-[0_8px_28px_rgba(15,23,42,0.09)] hover:-translate-y-0.5 transition-all duration-200 group">
              <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${f.color} flex items-center justify-center mb-3 shadow-sm`}>
                <ShieldCheck className="w-5 h-5 text-white" />
              </div>
              <p className="font-extrabold text-base text-[var(--ink)]">{f.name}</p>
              <p className="text-[11px] text-[var(--muted)] font-semibold mt-0.5 mb-2">{f.desc}</p>
              <p className="text-xs text-[var(--muted)] leading-relaxed">{f.detail}</p>
            </div>
          ))}
          {/* "More coming" card */}
          <div className="bg-[var(--card)] border border-dashed border-black/10 rounded-2xl p-5 flex flex-col items-start justify-center">
            <div className="w-10 h-10 rounded-xl bg-gray-100 flex items-center justify-center mb-3">
              <span className="text-lg font-black text-gray-400">+</span>
            </div>
            <p className="font-bold text-sm text-[var(--ink)]">More on the roadmap</p>
            <p className="text-xs text-[var(--muted)] mt-1 leading-relaxed">FedRAMP, SOX, and custom framework mapping coming soon.</p>
          </div>
        </div>
      </section>

      {/* ── Founder story ─────────────────────────────────────────────────────── */}
      <section className="bg-white/60 py-14 md:py-20 border-y border-black/5">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <p className="text-xs font-bold text-[var(--accent)] uppercase tracking-widest mb-4">Why we built this</p>
          <h2 className="text-2xl md:text-3xl font-extrabold mb-6 leading-tight">
            We spent 3 months on a manual SOC 2 audit.<br className="hidden md:block" /> Then built the tool we wished existed.
          </h2>
          <p className="text-[var(--muted)] text-base leading-relaxed mb-6 max-w-2xl mx-auto">
            Pulling screenshots from AWS at midnight. Chasing engineers for access logs. Rebuilding the same spreadsheet every quarter. Then handing an auditor a ZIP file of 400 screenshots and hoping for the best.
          </p>
          <p className="text-[var(--muted)] text-base leading-relaxed mb-8 max-w-2xl mx-auto">
            TraceLayer connects to your tools and collects that evidence automatically — every 24 hours, mapped to the right controls, ready to hand to an auditor in one click.
          </p>
          <div className="inline-flex items-center gap-3 bg-[var(--card)] border border-black/8 rounded-2xl px-5 py-3 shadow-sm">
            <div className="w-9 h-9 rounded-xl bg-[var(--accent)]/12 flex items-center justify-center text-sm font-bold text-[var(--accent)] shrink-0">N</div>
            <div className="text-left">
              <p className="text-xs font-bold text-[var(--ink)]">Nemanja Jeremenkovic</p>
              <p className="text-xs text-[var(--muted)]">Founder, TraceLayer</p>
            </div>
          </div>
        </div>
      </section>

      {/* ── Product stats strip ───────────────────────────────────────────────── */}
      <section className="border-b border-black/5 bg-[var(--bg)] py-12">
        <div className="max-w-4xl mx-auto px-6 grid grid-cols-1 sm:grid-cols-3 gap-10 text-center">
          <div>
            <div className="flex items-center justify-center gap-2 mb-1.5">
              <Plug className="w-4 h-4 text-[var(--accent)]" />
              <span className="text-2xl font-extrabold text-[var(--ink)]">120+</span>
            </div>
            <p className="text-xs text-[var(--muted)]">Integrations ready to connect on day one</p>
          </div>
          <div>
            <div className="flex items-center justify-center gap-2 mb-1.5">
              <RefreshCw className="w-4 h-4 text-[var(--accent)]" />
              <span className="text-2xl font-extrabold text-[var(--ink)]">24h</span>
            </div>
            <p className="text-xs text-[var(--muted)]">Automated evidence collection cycle — no manual work</p>
          </div>
          <div>
            <div className="flex items-center justify-center gap-2 mb-1.5">
              <ShieldCheck className="w-4 h-4 text-[var(--accent)]" />
              <span className="text-2xl font-extrabold text-[var(--ink)]">9</span>
            </div>
            <p className="text-xs text-[var(--muted)]">Frameworks mapped simultaneously from one integration set</p>
          </div>
        </div>
      </section>

      {/* ── Pricing ───────────────────────────────────────────────────────────── */}
      <section id="pricing" className="scroll-mt-16 bg-white/60 py-14 md:py-22">
        <div className="max-w-6xl mx-auto px-6">
          <div data-animate className="text-center mb-10 md:mb-14">
            <p className="text-xs font-bold text-[var(--accent)] uppercase tracking-widest mb-2">Pricing</p>
            <h2 className="text-2xl md:text-4xl font-extrabold leading-tight">
              Start free. Upgrade when you&apos;re ready.
            </h2>
            <p className="text-[var(--muted)] mt-3 text-sm max-w-xl mx-auto leading-relaxed">
              Built for seed, Series A, and Series B startups — not enterprises with six-figure compliance budgets. Start free, upgrade when you need AI, PDF reports, and all 9 frameworks including DPDP Act and CERT-In. $149/mo is literally one hour with a compliance consultant.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-stretch max-w-3xl mx-auto">

            {/* Free */}
            <div data-animate data-delay="100" className="bg-[var(--card)] border border-black/5 rounded-2xl p-7 shadow-[0_4px_20px_rgba(15,23,42,0.05)] flex flex-col">
              <p className="text-sm font-bold text-[var(--muted)] mb-1">Free</p>
              <div className="flex items-baseline gap-1 mb-1.5">
                <span className="text-4xl font-black text-[var(--ink)]">$0</span>
                <span className="text-sm text-[var(--muted)]">/mo</span>
              </div>
              <div className="inline-flex items-center gap-1.5 bg-gray-100 text-gray-500 text-[10px] font-semibold px-2.5 py-1 rounded-full mb-3 border border-gray-200 w-fit">
                No credit card required
              </div>
              <p className="text-xs mb-6 leading-relaxed text-[var(--muted)]">Everything you need to get started — SOC 2, automated evidence collection, risk, policies, and your whole team included.</p>
              <div className="space-y-2.5 mb-7 flex-1">
                {[
                  "SOC 2 framework",
                  "Up to 3 integrations",
                  "Up to 3 team members",
                  "Automated evidence collection",
                  "Risk register & vendor hub",
                  "Policy templates & training",
                  "JSON reports",
                  "Background & offboarding checks",
                ].map((f) => (
                  <div key={f} className="flex items-start gap-2.5">
                    <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5 text-[var(--accent)]" />
                    <span className="text-xs leading-snug text-[var(--ink)]">{f}</span>
                  </div>
                ))}
              </div>
              <Link href="/register" className="block text-center text-sm font-semibold py-2.5 rounded-xl transition-colors bg-[color:var(--ink)]/6 hover:bg-[color:var(--ink)]/10 text-[var(--ink)]">
                Get started free
              </Link>
            </div>

            {/* Growth */}
            <div data-animate data-delay="200" className="relative bg-slate-900 border border-slate-800 rounded-2xl p-7 shadow-[0_24px_60px_rgba(15,23,42,0.3)] flex flex-col">
              {/* Shimmer overlay */}
              <div className="absolute inset-0 rounded-2xl overflow-hidden pointer-events-none">
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/4 to-transparent -translate-x-full animate-shimmer" />
              </div>
              {/* Glow pulse */}
              <div className="absolute -inset-px rounded-2xl opacity-0 hover:opacity-100 transition-opacity duration-500 bg-gradient-to-br from-teal-500/20 via-transparent to-transparent pointer-events-none" />
              <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 z-10">
                <span className="bg-[var(--accent-warm)] text-white text-[10px] font-bold uppercase tracking-widest px-3 py-1.5 rounded-full shadow-sm whitespace-nowrap">
                  Most popular
                </span>
              </div>
              <p className="text-sm font-bold text-white/50 mb-1">Growth</p>
              <div className="flex items-baseline gap-1 mb-0.5">
                <span className="text-4xl font-black text-white">$149</span>
                <span className="text-sm text-white/40">/mo</span>
              </div>
              <p className="text-xs text-white/30 mb-1.5">≈ <span className="text-white/45 font-semibold">₹12,400/mo</span> · vs ₹75,000/mo for Sprinto</p>
              <div className="inline-flex items-center gap-1.5 bg-teal-500/15 text-teal-300 text-[10px] font-semibold px-2.5 py-1 rounded-full mb-3 border border-teal-500/20">
                <TrendingUp className="w-3 h-3" /> ≈ 30 min with a $300/hr consultant
              </div>
              <p className="text-xs mb-6 leading-relaxed text-white/45">AI features, PDF reports, all 9 frameworks incl. DPDP Act & CERT-In, Trust Center, unlimited integrations and team members.</p>
              <div className="space-y-2.5 mb-7 flex-1">
                {[
                  "Unlimited integrations (120+)",
                  "All 9 frameworks (incl. GDPR, DPDP Act, CERT-In, PCI DSS, NIST CSF)",
                  "PDF & CSV audit reports",
                  "AI Compliance Advisor",
                  "AI Questionnaire Autofill (17 data sources)",
                  "AI Audit Package",
                  "Data Flow Map (auto-mapped regulations & risk)",
                  "GDPR Privacy Suite (RoPA, SoA, Breach Register, SARs)",
                  "Incident, Vulnerability & Asset Management",
                  "Public Trust Center page",
                  "Unlimited team members",
                  "Priority support",
                  "and more →",
                ].map((f) => (
                  <div key={f} className="flex items-start gap-2.5">
                    {f === "and more →"
                      ? <span className="text-xs leading-snug text-white/30 italic pl-6">{f}</span>
                      : <><CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5 text-emerald-400" /><span className="text-xs leading-snug text-white/65">{f}</span></>
                    }
                  </div>
                ))}
              </div>
              <button
                onClick={handleGrowthCta}
                disabled={checkoutLoading}
                className="relative w-full flex items-center justify-center gap-2 text-sm font-semibold py-2.5 rounded-xl transition-all bg-[var(--accent)] hover:bg-[var(--accent-strong)] text-white disabled:opacity-60 shadow-[0_4px_14px_rgba(15,118,110,0.4)] hover:shadow-[0_6px_20px_rgba(15,118,110,0.6)] overflow-hidden group"
              >
                <span className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700" />
                {checkoutLoading ? (
                  <span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                ) : (
                  <Zap className="w-4 h-4" />
                )}
                {checkoutLoading ? "Opening checkout…" : "Get Growth — $149/mo"}
              </button>
              <p className="text-center text-[10px] text-white/25 mt-2">Cancel anytime · No contracts</p>
            </div>

          </div>

        </div>
      </section>

      {/* ── FAQ ───────────────────────────────────────────────────────────────── */}
      <section id="faq" className="scroll-mt-16 py-14 md:py-22 bg-[var(--bg)]">
        <div className="max-w-3xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-10 md:mb-14">
            <p className="text-xs font-bold text-[var(--accent)] uppercase tracking-widest mb-2">FAQ</p>
            <h2 className="text-2xl md:text-4xl font-extrabold">Got questions?</h2>
            <p className="text-[var(--muted)] mt-3 text-sm max-w-md mx-auto leading-relaxed">
              We&apos;ve answered the common ones below. For everything else, just reach out.
            </p>
          </div>
          <FaqAccordion items={FAQ} />
          <p className="text-center text-sm text-[var(--muted)] mt-8">
            Something else on your mind?{" "}
            <a href="mailto:hello@tracelayer.io" className="text-[var(--accent)] font-semibold hover:underline">
              Just ask us directly
            </a>
          </p>
        </div>
      </section>

      {/* ── Partner Program ───────────────────────────────────────────────────── */}
      <section id="partner" className="scroll-mt-16 py-14 md:py-22 bg-white border-t border-black/5">
        <div className="max-w-6xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-10 md:mb-14" data-animate>
            <p className="text-xs font-bold text-[var(--accent)] uppercase tracking-widest mb-2">Partner Program</p>
            <h2 className="text-2xl md:text-4xl font-extrabold text-[var(--ink)]">Three ways to partner with TraceLayer</h2>
            <p className="text-[var(--muted)] mt-3 text-sm max-w-xl mx-auto leading-relaxed">
              Consultants manage client compliance. Auditors receive pre-organized customers. Pen test firms get qualified referrals at exactly the right moment.
            </p>
          </div>

          {/* 3 track cards */}
          <div className="grid md:grid-cols-3 gap-5 mb-10">
            {[
              {
                icon: Users,
                badge: "Consultants & vCISOs",
                badgeColor: "bg-[color:var(--accent)]/10 text-[var(--accent)]",
                title: "Manage every client from one login",
                desc: "Provision dedicated workspaces for each client. Switch between them in one click. Share a Trust Center link. Bill your clients however you like — pay $99 per workspace, once.",
                cta: "Become a consultant partner",
                href: "/partners",
                primary: true,
              },
              {
                icon: FileText,
                badge: "Auditors",
                badgeColor: "bg-violet-50 text-violet-600",
                title: "Customers arrive pre-organized",
                desc: "When a customer hits 75%+ readiness, TraceLayer surfaces your firm. They share a read-only evidence link — no account needed on your end. Your fieldwork starts with everything already mapped.",
                cta: "List your firm",
                href: "/partners#auditors",
                primary: false,
              },
              {
                icon: Shield,
                badge: "Pen Test Firms",
                badgeColor: "bg-orange-50 text-orange-600",
                title: "Referrals at the exact right moment",
                desc: "SOC 2 requires an annual pen test. TraceLayer shows your firm when a customer's section is empty or overdue — warm leads with a clear deadline and a compliance reason to act.",
                cta: "List your firm",
                href: "/partners#pen-testers",
                primary: false,
              },
            ].map((item) => (
              <div key={item.title} data-animate className={`rounded-2xl p-6 border flex flex-col gap-4 ${item.primary ? "bg-[var(--bg)] border-black/5" : "bg-[var(--bg)] border-black/5"}`}>
                <div className="flex items-center gap-2">
                  <div className="w-9 h-9 rounded-xl bg-[color:var(--accent)]/10 flex items-center justify-center">
                    <item.icon className="w-4.5 h-4.5 text-[var(--accent)]" />
                  </div>
                  <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${item.badgeColor}`}>{item.badge}</span>
                </div>
                <div className="flex-1">
                  <h3 className="font-bold text-[var(--ink)] mb-2 leading-snug">{item.title}</h3>
                  <p className="text-sm text-[var(--muted)] leading-relaxed">{item.desc}</p>
                </div>
                <Link href={item.href} className="text-sm font-semibold text-[var(--accent)] hover:text-[color:var(--accent)]/80 flex items-center gap-1 transition-colors">
                  {item.cta} <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            ))}
          </div>

          {/* Consultant pricing + CTA */}
          <div data-animate className="bg-gradient-to-br from-brand-600 to-brand-900 rounded-3xl p-8 md:p-10 flex flex-col md:flex-row items-center justify-between gap-8 shadow-xl shadow-brand-600/20">
            <div>
              <p className="text-brand-200 text-xs font-bold uppercase tracking-widest mb-2">Consultant pricing</p>
              <h3 className="text-2xl md:text-3xl font-extrabold text-white mb-2">$99 per client workspace</h3>
              <p className="text-brand-200 text-sm leading-relaxed max-w-md">
                One-time per client. No monthly seat fees. Your partner account is free — only pay when you onboard a new client. Auditor and pen test listings are free.
              </p>
              <div className="flex flex-wrap gap-2 mt-4">
                {["First 3 clients free", "All frameworks included", "Trust Center per client", "Auditor access links"].map((f) => (
                  <span key={f} className="inline-flex items-center gap-1.5 text-xs font-medium text-brand-100 bg-white/10 border border-white/15 px-2.5 py-1 rounded-full">
                    <CheckCircle2 className="w-3 h-3 text-brand-300 shrink-0" />
                    {f}
                  </span>
                ))}
              </div>
            </div>
            <div className="flex flex-col gap-3 shrink-0 w-full md:w-auto">
              <Link
                href="/partners"
                className="inline-flex items-center justify-center gap-2 bg-white hover:bg-brand-50 text-brand-700 font-bold px-8 py-3.5 rounded-xl transition-colors text-sm shadow-sm whitespace-nowrap"
              >
                See the partner program
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                href="/partner-login"
                className="inline-flex items-center justify-center gap-2 bg-white/10 hover:bg-white/20 text-white border border-white/20 font-semibold px-8 py-3 rounded-xl transition-colors text-sm whitespace-nowrap"
              >
                Already a partner? Sign in
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ── Newsletter / Checklist capture ───────────────────────────────────── */}
      <section className="bg-white border-y border-gray-100 py-14 px-4">
        <div className="max-w-2xl mx-auto text-center">
          <p className="text-xs font-bold uppercase tracking-widest text-[var(--accent)] mb-3">Free resource</p>
          <h2 className="text-2xl font-extrabold text-gray-900 mb-2">
            Get the SOC 2 Starter Checklist
          </h2>
          <p className="text-gray-500 text-sm mb-6 max-w-md mx-auto">
            50+ controls, auditor language for each gap, and a prioritized fix order. Used by startup CTOs to prep for their first SOC 2. Free PDF, no fluff.
          </p>
          {newsletterSent ? (
            <div className="inline-flex items-center gap-2 bg-teal-50 text-teal-700 border border-teal-200 px-5 py-3 rounded-xl text-sm font-semibold">
              <CheckCircle2 className="w-4 h-4" />
              Check your inbox — checklist is on its way!
            </div>
          ) : (
            <form onSubmit={handleNewsletterSubmit} className="flex flex-col sm:flex-row gap-2 max-w-md mx-auto">
              <input
                type="email"
                required
                value={newsletterEmail}
                onChange={(e) => setNewsletterEmail(e.target.value)}
                placeholder="you@yourcompany.com"
                className="flex-1 text-sm border border-gray-200 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/30 focus:border-[var(--accent)] placeholder:text-gray-300"
              />
              <button
                type="submit"
                disabled={newsletterLoading}
                className="inline-flex items-center justify-center gap-2 bg-[var(--accent)] hover:bg-[var(--accent-strong)] disabled:opacity-60 text-white font-semibold px-6 py-3 rounded-xl transition-colors text-sm whitespace-nowrap"
              >
                {newsletterLoading ? (
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <>Get the checklist <ArrowRight className="w-4 h-4" /></>
                )}
              </button>
            </form>
          )}
          <p className="text-xs text-gray-400 mt-3">No spam. Unsubscribe anytime.</p>
        </div>
      </section>

      {/* ── Final CTA ─────────────────────────────────────────────────────────── */}
      <section className="bg-slate-900 py-16 md:py-24 relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_rgba(15,118,110,0.3),_transparent_70%)] pointer-events-none" />
        <div className="absolute top-0 right-0 w-80 h-80 rounded-full bg-teal-500/10 blur-3xl -translate-y-1/2 translate-x-1/2 pointer-events-none" />
        <div className="max-w-2xl mx-auto px-6 text-center relative">
          <div className="inline-flex items-center gap-2 bg-white/10 text-teal-300 text-xs font-semibold px-3.5 py-1.5 rounded-full mb-6 border border-white/10">
            <span className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-pulse" />
            Free to start · No credit card required
          </div>
          <h2 className="text-3xl md:text-5xl font-extrabold text-white mb-5 leading-tight">
            Your next audit<br />starts now.
          </h2>
          <p className="text-white/60 mb-8 text-sm leading-relaxed max-w-md mx-auto">
            Create your account and get your full compliance program running in minutes — evidence collection, risk register, policies, training, vendors, and a live readiness score.
          </p>
          <Link
            href="/register"
            className="inline-flex items-center gap-2 bg-[var(--accent)] hover:bg-[var(--accent-strong)] text-white font-bold px-8 py-3.5 rounded-xl transition-colors text-sm shadow-[0_0_32px_rgba(15,118,110,0.4)]"
          >
            Get started free <ArrowRight className="w-4 h-4" />
          </Link>
          <p className="text-white/30 text-xs mt-4">Setup in 5 minutes · SOC 2 · ISO 27001 · HIPAA · GDPR · PCI DSS · CCPA · NIST CSF</p>
        </div>
      </section>

      {/* ── Footer ────────────────────────────────────────────────────────────── */}
      <footer className="bg-slate-950 text-slate-400">
        {/* Top bar — brand + key stats */}
        <div className="border-b border-white/6">
          <div className="max-w-6xl mx-auto px-6 py-5 flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-2.5">
              <Image src="/logo-icon.png" alt="TraceLayer" width={22} height={22} className="rounded-md" />
              <span className="font-extrabold text-sm text-white tracking-tight">TraceLayer</span>
            </div>
            <div className="flex flex-wrap items-center gap-5 sm:gap-8">
              {[
                { value: "120+", label: "integrations" },
                { value: "7",    label: "frameworks"   },
                { value: "24h",  label: "sync cadence" },
              ].map(({ value, label }) => (
                <div key={label} className="flex items-baseline gap-1">
                  <span className="text-sm font-black text-white">{value}</span>
                  <span className="text-xs text-slate-500">{label}</span>
                </div>
              ))}
            </div>
            <div className="hidden lg:flex items-center gap-3">
              {["SOC 2", "ISO 27001", "HIPAA", "GDPR", "PCI DSS"].map((f) => (
                <span key={f} className="text-[10px] font-semibold text-slate-500 border border-white/8 px-2 py-0.5 rounded-full">{f}</span>
              ))}
            </div>
          </div>
        </div>

        {/* Main grid */}
        <div className="max-w-6xl mx-auto px-6 pt-12 pb-10">
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-x-8 gap-y-10 mb-12">
            {/* Brand */}
            <div className="col-span-2">
              <p className="text-sm text-slate-300 leading-relaxed mb-5 max-w-xs">
                The compliance platform for seed & Series A/B startup CTOs closing enterprise deals — without a compliance team or a $20K Vanta contract.
              </p>
              <div className="flex items-center gap-2.5">
                {[
                  { icon: Github,   href: "https://github.com/Jeremenkovic/TraceLayer", label: "GitHub"   },
                  { icon: Twitter,  href: "https://twitter.com/tracelayer",              label: "Twitter"  },
                  { icon: Linkedin, href: "https://linkedin.com/company/tracelayer",     label: "LinkedIn" },
                ].map(({ icon: Icon, href, label }) => (
                  <a key={label} href={href} target="_blank" rel="noopener noreferrer" aria-label={label}
                    className="w-8 h-8 rounded-lg bg-white/5 hover:bg-white/10 border border-white/8 flex items-center justify-center transition-all group">
                    <Icon className="w-3.5 h-3.5 text-slate-500 group-hover:text-white transition-colors" />
                  </a>
                ))}
              </div>
            </div>

            {/* Product */}
            <div>
              <p className="text-[11px] font-bold text-slate-300 uppercase tracking-widest mb-4">Product</p>
              <ul className="space-y-3">
                {[
                  { label: "How it works", href: "#how-it-works" },
                  { label: "Features",     href: "#features"     },
                  { label: "Pricing",      href: "#pricing"      },
                  { label: "Integrations", href: "#integrations" },
                  { label: "FAQ",          href: "#faq"          },
                ].map((l) => (
                  <li key={l.label}>
                    <a href={l.href} onClick={(e) => smoothScroll(e, l.href)}
                      className="text-xs text-slate-500 hover:text-slate-200 transition-colors">
                      {l.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>

            {/* Company */}
            <div>
              <p className="text-[11px] font-bold text-slate-300 uppercase tracking-widest mb-4">Company</p>
              <ul className="space-y-3">
                {[
                  { label: "Sign in",          href: "/login"         },
                  { label: "Get started",       href: "/register"      },
                  { label: "Partner program",   href: "/partners"      },
                  { label: "Partner login",     href: "/partner-login" },
                ].map((l) => (
                  <li key={l.label}>
                    {l.href.startsWith("#") ? (
                      <a href={l.href} onClick={(e) => smoothScroll(e, l.href)}
                        className="text-xs text-slate-500 hover:text-slate-200 transition-colors">
                        {l.label}
                      </a>
                    ) : (
                      <Link href={l.href} className="text-xs text-slate-500 hover:text-slate-200 transition-colors">
                        {l.label}
                      </Link>
                    )}
                  </li>
                ))}
              </ul>
            </div>

            {/* Legal */}
            <div>
              <p className="text-[11px] font-bold text-slate-300 uppercase tracking-widest mb-4">Legal</p>
              <ul className="space-y-3">
                {[
                  { label: "Privacy Policy",   href: "/privacy"  },
                  { label: "Terms of Service", href: "/terms"    },
                  { label: "DPA",              href: "/dpa"      },
                  { label: "Security",         href: "/security" },
                  { label: "Status",           href: "/status"   },
                ].map((l) => (
                  <li key={l.label}>
                    <Link href={l.href} className="text-xs text-slate-500 hover:text-slate-200 transition-colors">
                      {l.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Bottom bar */}
          <div className="border-t border-white/6 pt-6 flex flex-col sm:flex-row items-center justify-between gap-3">
            <p className="text-xs text-slate-600">© {new Date().getFullYear()} TraceLayer, Inc. All rights reserved.</p>
            <p className="text-xs text-slate-600">Built for seed & Series A/B startup CTOs closing enterprise deals.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
