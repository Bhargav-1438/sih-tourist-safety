/**
 * Reusable Leaflet map foundation.
 *
 * Later prompts add <Marker />, <Circle />, and <Popup /> children on top of
 * this component; it deliberately knows nothing about risk zones, incidents,
 * SOS events, or patrols.
 */
import type { ReactNode } from "react";
import { MapContainer, TileLayer } from "react-leaflet";
import "leaflet/dist/leaflet.css";

interface MapViewProps {
  /** [latitude, longitude] - Leaflet order. Defaults to the Vijayawada demo geography. */
  center?: [number, number];
  zoom?: number;
  className?: string;
  children?: ReactNode;
}

const DEFAULT_CENTER: [number, number] = [16.5062, 80.6480];
const DEFAULT_ZOOM = 12;

export default function MapView({
  center = DEFAULT_CENTER,
  zoom = DEFAULT_ZOOM,
  className,
  children,
}: MapViewProps) {
  return (
    <MapContainer center={center} zoom={zoom} className={className ?? "map-view"}>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {children}
    </MapContainer>
  );
}
