import { createContext, useContext, useState, forwardRef } from 'react'
import { ChevronDown } from 'lucide-react'

const SelectContext = createContext()

const Select = ({ value, onValueChange, defaultValue, children }) => {
  const [internalValue, setInternalValue] = useState(defaultValue)
  const [isOpen, setIsOpen] = useState(false)
  
  const currentValue = value !== undefined ? value : internalValue
  
  const handleValueChange = (newValue) => {
    if (value === undefined) {
      setInternalValue(newValue)
    }
    onValueChange?.(newValue)
    setIsOpen(false)
  }

  return (
    <SelectContext.Provider value={{ 
      value: currentValue, 
      onValueChange: handleValueChange,
      isOpen,
      setIsOpen
    }}>
      <div className="relative">
        {children}
      </div>
    </SelectContext.Provider>
  )
}

const SelectTrigger = forwardRef(({ className = '', children, ...props }, ref) => {
  const context = useContext(SelectContext)
  
  return (
    <button
      ref={ref}
      className={`flex h-10 w-full items-center justify-between rounded-md border border-gray-200 bg-white px-3 py-2 text-sm ring-offset-white placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-gray-950 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${className}`}
      onClick={() => context?.setIsOpen(!context.isOpen)}
      {...props}
    >
      {children}
      <ChevronDown className="h-4 w-4 opacity-50" />
    </button>
  )
})
SelectTrigger.displayName = 'SelectTrigger'

const SelectValue = forwardRef(({ placeholder, className = '', ...props }, ref) => {
  const context = useContext(SelectContext)
  
  return (
    <span
      ref={ref}
      className={className}
      {...props}
    >
      {context?.value || placeholder}
    </span>
  )
})
SelectValue.displayName = 'SelectValue'

const SelectContent = forwardRef(({ className = '', children, ...props }, ref) => {
  const context = useContext(SelectContext)
  
  if (!context?.isOpen) return null
  
  return (
    <div
      ref={ref}
      className={`absolute top-full left-0 z-50 w-full min-w-[8rem] overflow-hidden rounded-md border border-gray-200 bg-white text-gray-950 shadow-md animate-in fade-in-0 zoom-in-95 ${className}`}
      {...props}
    >
      <div className="p-1">
        {children}
      </div>
    </div>
  )
})
SelectContent.displayName = 'SelectContent'

const SelectItem = forwardRef(({ className = '', value, children, ...props }, ref) => {
  const context = useContext(SelectContext)
  
  return (
    <div
      ref={ref}
      className={`relative flex w-full cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none hover:bg-gray-100 focus:bg-gray-100 ${className}`}
      onClick={() => context?.onValueChange?.(value)}
      {...props}
    >
      {children}
    </div>
  )
})
SelectItem.displayName = 'SelectItem'

export { Select, SelectTrigger, SelectValue, SelectContent, SelectItem }

