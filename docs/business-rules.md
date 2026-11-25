# Reglas de negocio

1. El rol de una cuenta se determina en cada sala. El propietario también es
   administrador local. Las operaciones con otros horarios son de solo lectura.
2. Una sala tiene un código único. El ingreso repetido conserva la membresía
   existente y el número máximo de integrantes se comprueba en la transacción.
3. Un horario pertenece a una membresía y consta de 70 celdas. Un borrador no
   aporta al cálculo. La edición se confirma con la versión esperada.
4. El peso de un bloque suma las ocupaciones confirmadas. La disponibilidad
   cuenta integrantes confirmados que no están ocupados. Los demás quedan
   pendientes, por separado.
5. Eliminar una cuenta revoca las sesiones. Si posee una sala compartida, debe
   confirmar una transferencia o el cierre. La operación confirma todos
   los cambios juntos.
