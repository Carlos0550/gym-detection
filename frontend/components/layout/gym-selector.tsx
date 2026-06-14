"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useGym } from "@/hooks/use-auth";

export function GymSelector() {
  const { gymId, setGymId, manageableGyms } = useGym();

  if (manageableGyms.length <= 1) {
    const gym = manageableGyms[0];
    if (!gym) return null;
    return (
      <p className="truncate rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm font-medium">
        {gym.gym_name}
      </p>
    );
  }

  return (
    <Select value={gymId ?? undefined} onValueChange={setGymId}>
      <SelectTrigger className="w-full">
        <SelectValue placeholder="Seleccionar gimnasio" />
      </SelectTrigger>
      <SelectContent>
        {manageableGyms.map((gym) => (
          <SelectItem key={gym.gym_id} value={gym.gym_id}>
            {gym.gym_name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
