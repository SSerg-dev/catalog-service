export const dynamic = "force-dynamic";

type Product = {
  id: number;
  title: string;
  image_url: string;
  created_at: string;
};


async function getProducts(): Promise<Product[]> {
  const apiUrl = process.env.INTERNAL_API_URL ?? "http://localhost:8000";
  const response = await fetch(`${apiUrl}/api/products`, { cache: "no-store" });

  if (!response.ok) {
    throw new Error(`Catalog API returned ${response.status}`);
  }

  return response.json();
}


export default async function CatalogPage() {
  let products: Product[] = [];
  let unavailable = false;

  try {
    products = await getProducts();
  } catch {
    unavailable = true;
  }

  return (
    <main>
      <h1>Каталог</h1>

      {unavailable ? (
        <p role="alert">Каталог временно недоступен. Попробуйте обновить страницу.</p>
      ) : products.length === 0 ? (
        <p>Товаров пока нет.</p>
      ) : (
        <ul className="products">
          {products.map((product) => (
            <li key={product.id} className="product">
              <img src={product.image_url} alt="" loading="lazy" />
              <h2>{product.title}</h2>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}

