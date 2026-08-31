import { useQuery } from "@tanstack/react-query";
import { Flavours } from "@/lib/api";

export function useFlavours() {
  return useQuery({ queryKey: ["flavours"], queryFn: Flavours.list });
}

export function useFlavourDisplayName(flavourId: string | undefined) {
  const { data: flavours } = useFlavours();
  if (!flavourId) return undefined;
  return flavours?.find((f) => f.id === flavourId)?.display_name ?? flavourId;
}
