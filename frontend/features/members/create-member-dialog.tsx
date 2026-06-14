"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Check, Copy } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { createGymUser } from "@/lib/api/users";
import type { ApiError, UserCreatedResponse } from "@/lib/types/api";

const IDENTIFIER_MESSAGE = "Ingresá email o DNI para identificar al miembro";

const schema = z
  .object({
    full_name: z.string().min(2, "Mínimo 2 caracteres"),
    email: z
      .string()
      .transform((value) => value.trim())
      .pipe(z.union([z.literal(""), z.email("Email inválido")])),
    document: z
      .string()
      .transform((value) => value.trim())
      .pipe(z.union([z.literal(""), z.string().min(3, "Mínimo 3 caracteres")])),
  })
  .superRefine((data, ctx) => {
    if (!data.email && !data.document) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: IDENTIFIER_MESSAGE,
        path: ["email"],
      });
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: IDENTIFIER_MESSAGE,
        path: ["document"],
      });
    }
  });

type FormValues = z.infer<typeof schema>;

type SuccessState = {
  member: UserCreatedResponse;
  password: string;
};

type Props = {
  gymId: string;
};

function isPlaceholderEmail(email: string) {
  return email.endsWith("@gym-detection.internal");
}

function buildCreatePayload(values: FormValues) {
  return {
    full_name: values.full_name,
    kind_role: "client" as const,
    ...(values.email ? { email: values.email } : {}),
    ...(values.document ? { document: values.document } : {}),
  };
}

export function CreateMemberDialog({ gymId }: Props) {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [success, setSuccess] = useState<SuccessState | null>(null);
  const [copied, setCopied] = useState(false);
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      full_name: "",
      email: "",
      document: "",
    },
  });

  const resetDialog = () => {
    form.reset();
    setSuccess(null);
    setCopied(false);
  };

  const handleOpenChange = (nextOpen: boolean) => {
    setOpen(nextOpen);
    if (!nextOpen) {
      resetDialog();
    }
  };

  const mutation = useMutation({
    mutationFn: (values: FormValues) => createGymUser(gymId, buildCreatePayload(values)),
    onSuccess: (member) => {
      queryClient.invalidateQueries({ queryKey: ["members", gymId] });
      const password = member.temporary_password;
      if (!password) {
        toast.success("Miembro creado", { duration: 6000 });
        resetDialog();
        setOpen(false);
        return;
      }
      setSuccess({ member, password });
    },
    onError: (error: ApiError) => {
      toast.error(error.detail, { duration: 12000 });
    },
  });

  const handleCopyPassword = async () => {
    if (!success?.password) return;
    try {
      await navigator.clipboard.writeText(success.password);
      setCopied(true);
      toast.success("Contraseña copiada");
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error("No pudimos copiar la contraseña");
    }
  };

  const showEmail =
    success?.member.email && !isPlaceholderEmail(success.member.email);

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button>Nuevo miembro</Button>
      </DialogTrigger>
      <DialogContent>
        {success ? (
          <>
            <DialogHeader>
              <div className="section-tag">Miembros · Listo</div>
              <DialogTitle className="mt-2">Miembro creado</DialogTitle>
              <DialogDescription>
                Compartile estas credenciales a{" "}
                <strong className="text-foreground">{success.member.full_name}</strong>.
                La contraseña no se vuelve a mostrar.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4 rounded-lg border border-border/60 bg-muted/30 p-4">
              {success.member.document ? (
                <div>
                  <p className="text-xs uppercase tracking-wide text-muted-foreground">
                    DNI
                  </p>
                  <p className="font-medium">{success.member.document}</p>
                </div>
              ) : null}
              {showEmail ? (
                <div>
                  <p className="text-xs uppercase tracking-wide text-muted-foreground">
                    Email
                  </p>
                  <p className="font-medium">{success.member.email}</p>
                </div>
              ) : null}
              <div>
                <p className="text-xs uppercase tracking-wide text-muted-foreground">
                  Contraseña temporal
                </p>
                <div className="mt-1 flex items-center gap-2">
                  <code className="flex-1 rounded-md bg-background px-3 py-2 font-mono text-sm">
                    {success.password}
                  </code>
                  <Button
                    type="button"
                    variant="outline"
                    size="icon"
                    onClick={handleCopyPassword}
                    aria-label="Copiar contraseña"
                  >
                    {copied ? (
                      <Check className="size-4 text-green-600" />
                    ) : (
                      <Copy className="size-4" />
                    )}
                  </Button>
                </div>
              </div>
              {!showEmail ? (
                <p className="text-sm text-muted-foreground">
                  Este miembro no tiene email. Guardá la contraseña por si necesita
                  acceder al panel.
                </p>
              ) : null}
            </div>

            <DialogFooter>
              <Button
                onClick={() => {
                  resetDialog();
                  setOpen(false);
                }}
              >
                Listo
              </Button>
            </DialogFooter>
          </>
        ) : (
          <>
            <DialogHeader>
              <div className="section-tag">Miembros · Nuevo</div>
              <DialogTitle className="mt-2">Crear miembro</DialogTitle>
              <DialogDescription>
                Completá los datos del miembro. Generamos una contraseña temporal
                automáticamente.
              </DialogDescription>
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
                        <Input type="email" autoComplete="off" {...field} />
                      </FormControl>
                      <FormDescription>Opcional si completás el DNI.</FormDescription>
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
                        <Input autoComplete="off" {...field} />
                      </FormControl>
                      <FormDescription>Opcional si completás el email.</FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <Button type="submit" disabled={mutation.isPending}>
                  {mutation.isPending ? "Creando..." : "Crear"}
                </Button>
              </form>
            </Form>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
