export interface Sector {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
}

export interface SectorListResponse {
  items: Sector[];
  total: number;
}
