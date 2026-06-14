"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { updateGymUser } from "@/lib/api/users";
import type { ApiError, GymClient } from "@/lib/types/api";

const schema = z.object({
  document: z.string().min(3, "Mínimo 3 caracteres"),
});

type FormValues = z.infer<typeof schema>;

type Props = {
  gymId: string;
  member: GymClient | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

export function EditMemberDialog({ gymId, member, open, onOpenChange }: Props) {
  const queryClient = useQueryClient();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { document: "" },
  });

  useEffect(() => {
    if (member) {
      form.reset({ document: member.document ?? "" });
    }
  }, [member, form]);

  const mutation = useMutation({
    mutationFn: (values: FormValues) =>
      updateGymUser(gymId, member!.id, { document: values.document }),
    onSuccess: () => {
      toast.success("Miembro actualizado");
      queryClient.invalidateQueries({ queryKey: ["members", gymId] });
      onOpenChange(false);
    },
    onError: (error: ApiError) => {
      toast.error(error.detail);
    },
  });

  if (!member) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <div className="section-tag">Miembros · Editar</div>
          <DialogTitle className="mt-2">Editar miembro</DialogTitle>
        </DialogHeader>
        <p className="text-sm text-muted-foreground">{member.full_name}</p>
        <Form {...form}>
          <form
            onSubmit={form.handleSubmit((values) => mutation.mutate(values))}
            className="space-y-4"
          >
            <FormField
              control={form.control}
              name="document"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>DNI / Documento</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? "Guardando..." : "Guardar"}
            </Button>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
