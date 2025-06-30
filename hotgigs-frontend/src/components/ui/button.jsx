import { forwardRef } from 'react'

const buttonVariants = {
  default: 'bg-gray-900 text-gray-50 hover:bg-gray-900/90',
  destructive: 'bg-red-500 text-gray-50 hover:bg-red-500/90',
  outline: 'border border-gray-200 bg-white hover:bg-gray-100 hover:text-gray-900',
  secondary: 'bg-gray-100 text-gray-900 hover:bg-gray-100/80',
  ghost: 'hover:bg-gray-100 hover:text-gray-900',
  link: 'text-gray-900 underline-offset-4 hover:underline'
}

const buttonSizes = {
  default: 'h-10 px-4 py-2',
  sm: 'h-9 rounded-md px-3',
  lg: 'h-11 rounded-md px-8',
  icon: 'h-10 w-10'
}

const Button = forwardRef(({ 
  className = '', 
  variant = 'default', 
  size = 'default', 
  disabled = false,
  ...props 
}, ref) => {
  return (
    <button
      ref={ref}
      className={`inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-white transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-950 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 ${buttonVariants[variant]} ${buttonSizes[size]} ${className}`}
      disabled={disabled}
      {...props}
    />
  )
})
Button.displayName = 'Button'

export { Button }

