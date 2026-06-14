"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
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
import { createGymUser } from "@/lib/api/users";
import type { ApiError } from "@/lib/types/api";

const schema = z.object({
  full_name: z.string().min(2, "Mínimo 2 caracteres"),
  email: z.email("Email inválido"),
  password: z.string().min(8, "Mínimo 8 caracteres"),
  document: z.string().min(3, "DNI requerido"),
});

type FormValues = z.infer<typeof schema>;

type Props = {
  gymId: string;
};

export function CreateMemberDialog({ gymId }: Props) {
  const queryClient = useQueryClient();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      full_name: "",
      email: "",
      password: "",
      document: "",
    },
  });

  const mutation = useMutation({
    mutationFn: (values: FormValues) =>
      createGymUser(gymId, { ...values, kind_role: "client" }),
    onSuccess: () => {
      toast.success("Miembro creado");
      queryClient.invalidateQueries({ queryKey: ["members", gymId] });
      form.reset();
    },
    onError: (error: ApiError) => {
      toast.error(error.detail);
    },
  });

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button>Nuevo miembro</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <div className="section-tag">Miembros · Nuevo</div>
          <DialogTitle className="mt-2">Crear miembro</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form
            onSubmit={form.handleSubmit((values) => mutation.mutate(values))}
            className="space-y-4"
          >
            <FormField
              control={form.control}
              name="full_name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Nombre completo</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email</FormLabel>
                  <FormControl>
                    <Input type="email" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
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
            <FormField
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Contraseña temporal</FormLabel>
                  <FormControl>
                    <Input type="password" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? "Creando..." : "Crear"}
            </Button>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
