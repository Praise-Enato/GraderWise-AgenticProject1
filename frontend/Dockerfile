# Use an official Node.js runtime as a parent image
FROM node:20-alpine

# Set the working directory in the container
WORKDIR /app

# Copy package.json and package-lock.json first to leverage Docker cache
COPY package.json package-lock.json ./

# Install dependencies (use ci for clean install based on lockfile)
RUN npm install

# Copy the rest of the application code
COPY . .

# Bake public build-time config into the Next.js build.
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

# Disable the Educator workspace in the demo deploy (set to "false"). Unset or any
# other value keeps it enabled (dev default).
ARG NEXT_PUBLIC_EDUCATOR_ENABLED
ENV NEXT_PUBLIC_EDUCATOR_ENABLED=${NEXT_PUBLIC_EDUCATOR_ENABLED}

# Build the Next.js application
RUN npm run build

# Expose port 3000 for the application
EXPOSE 3000

# Start the application
CMD ["npm", "start"]
