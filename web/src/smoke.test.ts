import { createElement } from "react";
import { renderToString } from "react-dom/server";
import { expect, test } from "vitest";
import App from "./App";

test("App renders its heading", () => {
  expect(renderToString(createElement(App))).toContain("Property Swipe");
});
