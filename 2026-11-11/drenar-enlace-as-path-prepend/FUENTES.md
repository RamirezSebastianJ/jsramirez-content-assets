# Fuentes
- AWS Architecture Blog, "How DeepL keeps closest-exit routing during maintenance with AWS Cloud WAN" (9 nov 2026): https://aws.amazon.com/blogs/architecture/how-deepl-keeps-closest-exit-routing-during-maintenance-with-aws-cloud-wan/
- Lo afirmado sobre DeepL (drenar un enlace de Direct Connect para mantenimiento, sin pérdida de paquetes ni reenrutamiento entre regiones, con AWS Cloud WAN y AS_PATH prepend) viene del resumen del índice del blog (https://aws.amazon.com/blogs/architecture/). En esta ejecución NO se pudo abrir el artículo completo (WebFetch sin permiso): verificar contra el original antes de grabar.
- Lo demás (prepend alarga la ruta; en BGP una ruta más larga es menos preferida) es conocimiento general de BGP, sin cifras.
